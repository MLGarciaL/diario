def busqueda3(Palabra):
    def LaVentana(url,Palabra):
            import requests
            from bs4 import BeautifulSoup
            # Realizar la solicitud GET a la URL de la noticia
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url,headers=headers)
            # Parsear el contenido HTML de la página
            soup = BeautifulSoup(response.text, 'html.parser')

            #ETIQUETAS
            entry_tags = soup.find('div', class_='tags')

            etiquetas = ''
            if entry_tags:
                for etiqueta in entry_tags.find_all('a'):
                    if etiqueta.text != '':
                        etiquetas += f"{etiqueta.text}\n"
                        etiquetas += ','
            


            # TEXTO NOTICIA
            titulo_noticia = soup.find('div', class_='single_post_heading')
            texto_noticia = soup.find('div', class_='quomodo-content-container')

            texto1 = titulo_noticia.text
            texto1 = ' '.join(texto1.replace('"', '').replace('/', '-').replace(':', '').split())
            texto2 = texto_noticia.get_text()
            texto2 = ' '.join(texto2.split())



            #FECHA NOTICIA
            fecha_hora_elemento = soup.find('div', class_='col-12')

            li_tag = soup.find('li', class_='post-read-time')
            fecha=''
            if li_tag:

                i_tag = li_tag.find_previous_sibling().text.strip()

                if i_tag:
                    fecha =i_tag.strip()

            return Palabra, etiquetas ,fecha , texto1, texto2

    def noticia(Palabra):
        Diario='La Ventana'
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime

        numpagina = 1
        url_base = "https://diariolaventana.com.ar/page/{}/?s={}"

        PalabraA= Palabra.replace(' ', '+')

        data_lines = []

        while True:

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url_base.format(numpagina, PalabraA), headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            entry_data_divs = soup.find_all('a', class_='readmore')

            for entry_data_div in entry_data_divs:
                article_url = entry_data_div['href']
                url = article_url
                                
                Palabra, etiquetas, fecha, texto1, texto2 = LaVentana(url, Palabra)

                fecha_datetime = datetime.strptime(fecha, '%d/%m/%Y')
                fecha= fecha_datetime.strftime('%Y/%m/%d')
                if fecha_datetime >= datetime(2024, 1, 1):

                    data_line = ' | '.join([Palabra, etiquetas, fecha, texto1, texto2,Diario, url])
                    data_lines.append(data_line)

                    continue  
                else:
                    break
            else:
                numpagina += 1
                continue
            
            break
        return data_lines

    data_lines=noticia(Palabra)

    import pandas as pd

    palabra_list = []
    etiquetas_list = []
    fecha_list = []
    titulo_list = []
    contenido_list = []
    diario_list = []
    url_list = []


    for line in data_lines:
        elements = line.split('|')
        palabra_list.append(elements[0].strip())
        etiquetas_list.append(elements[1].strip())
        fecha_list.append(elements[2].strip())
        titulo_list.append(elements[3].strip())
        contenido_list.append(elements[4].strip())
        diario_list.append(elements[5].strip())
        url_list.append(elements[6].strip())


    df = pd.DataFrame({
        'Palabra': palabra_list,
        'Etiquetas': etiquetas_list,
        'Fecha': fecha_list,
        'Título': titulo_list,
        'Contenido': contenido_list,
        'Diario': diario_list,
        'URL': url_list
    })

    print(df)
        
    import mysql.connector

    # Conexión a MySQL
    conn_mysql = mysql.connector.connect(
        host='localhost',
        user='root',
        password=' ',
        database='noticias'
    )

    cursor_mysql = conn_mysql.cursor()

    try:
        for index, row in df.iterrows():
            # Define the SQL INSERT statement with placeholders
            sql_insert = '''
                INSERT INTO noticias_new (Palabra, Etiquetas, Fecha, Título, Contenido, Diario, URL)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''

            # Extract values from the DataFrame row
            values = (
                row['Palabra'],
                row['Etiquetas'],
                row['Fecha'],
                row['Título'],
                row['Contenido'],
                row['Diario'],
                row['URL']
            )

            cursor_mysql.execute(sql_insert, values)

            # Optionally, update a flag in the DataFrame to indicate successful migration
            df.at[index, 'migrado'] = 1

        # Commit the transaction to persist changes in the database
        conn_mysql.commit()

    except Exception as e:
        print(f"Error occurred: {e}")
        conn_mysql.rollback()  # Roll back changes if an error occurs

    finally:
        # Close the cursor and connection
        cursor_mysql.close()
        conn_mysql.close()
