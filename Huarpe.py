def busqueda2(Palabra):
    def Huarpe(url,Palabra):
            import requests
            from bs4 import BeautifulSoup
            from datetime import datetime
            import locale

            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            # Realizar la solicitud GET a la URL de la noticia
            response = requests.get(url)
            # Parsear el contenido HTML de la página
            soup = BeautifulSoup(response.text, 'html.parser')


            #ETIQUETAS
            entry_tags = soup.find('div', class_='tags')
            i=0
            etiquetas = ''
            if entry_tags:
                for etiqueta in entry_tags.find_all('a'):
                    if etiqueta.text != '':
                        etiquetas += f"{etiqueta.text}\n"
                        i+= len(etiqueta.text.split())
                        etiquetas += ','
            


            # TEXTO NOTICIA
            titulo_noticia = soup.find('h1', class_='nota-titulo')
            texto_noticia = soup.find('div', class_='news-amp-body')

            # Eliminar el contenido dentro de la clase 'link-nota-propia' si está presente
            link_nota_propia = texto_noticia.find('div', class_='link-nota-propia')
            if link_nota_propia:
                link_nota_propia.decompose() 

            # Eliminar el contenido dentro de la clase 'container-spot' si está presente
            container_spot = texto_noticia.find('div', class_='container-spot')
            if container_spot:
                container_spot.decompose() 

            texto1 = titulo_noticia.get_text()
            texto1 = ' '.join(texto1.replace('"', '').replace('/', '-').replace(':', '').replace('|', '').split())
            texto2 = texto_noticia.get_text()
            texto2 = ' '.join(texto2.replace('"', '').replace('/', '-').replace(':', '').replace('|', '').split())


            #FECHA NOTICIA
            fecha_hora_elemento = soup.find('div', class_='date')
            if fecha_hora_elemento is None:
                fecha_hora_elemento = soup.find('div', class_='fecha view_mobile')
                if fecha_hora_elemento is None:
                    return None
            
            fecha_str=fecha_hora_elemento.get_text()
            if 'hace' in fecha_str.lower():
                fecha =  datetime.now().strftime('%Y-%m-%d')
            else:
                fecha = datetime.strptime(fecha_str, "%d de %B de %Y")
                fecha = fecha.strftime("%Y-%m-%d")
            
            return Palabra, etiquetas ,fecha , texto1, texto2

    def noticia(Palabra):
        Diario='Huarpe'
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime

        numpagina = 0
        url_base = "https://www.diariohuarpe.com/jbuscar/{}/{}"

        data_lines = []

        PalabraA= Palabra.replace(' ', '%20')

        while True:
            response = requests.get(url_base.format(PalabraA, numpagina))
            soup = BeautifulSoup(response.text, 'html.parser')
            
            entry_data_divs = soup.find_all('div', class_='titulo')
            
            for entry_data_div in entry_data_divs:
                article_url = entry_data_div.find('a')['href']
                url = 'https://www.diariohuarpe.com' + article_url

                if Huarpe(url, Palabra) is not None:
                    Palabra, etiquetas, fecha, texto1, texto2 = Huarpe(url, Palabra)

                    fecha_datetime = datetime.strptime(fecha, '%Y-%m-%d')
                    fecha= fecha_datetime.strftime('%Y/%m/%d')
                    if fecha_datetime >= datetime(2024, 4, 19):

                        data_line = ' | '.join([Palabra, etiquetas, fecha, texto1, texto2, Diario, url])
                        data_lines.append(data_line)

                        continue  
                    else:
                        break
            else:
                numpagina += 9
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
