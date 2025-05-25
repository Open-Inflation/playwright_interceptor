import os
import glob
import sys
import argparse


def generate_docs_index(docs_dir: str = "docs", project_name: str = "Default Project") -> bool:
    """
    Генерирует индексную страницу для HTML документации.
    
    Args:
        docs_dir: Путь к директории с документацией
        project_name: Имя проекта

    Returns:
        True если индексная страница была успешно создана, False в противном случае
    """
    if not os.path.exists(docs_dir):
        print(f"Директория {docs_dir} не найдена. Проверьте путь к директории.")
        return False

    # Получаем список HTML файлов
    html_files = glob.glob(os.path.join(docs_dir, "*.html"))

    # Создаем содержимое индексной страницы
    index_content = """<!DOCTYPE html>
<html>
<head>
    <title>""" + project_name + """ / Response API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css?family=Overpass:300,400,600,800">
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="schema_doc.css">
    <style>
        body { padding: 20px; font-family: 'Overpass', sans-serif; }
        h1 { margin-bottom: 30px; }
        .schema-list { margin-top: 20px; }
        .footer { margin-top: 30px; text-align: center; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>""" + project_name + """ / Response API Documentation</h1>
        <div class="schema-list">
            <h2>Доступные схемы:</h2>
            <ul class="list-group">
"""

    # Добавляем ссылки на каждую схему
    for html_file in sorted(html_files):
        if "index.html" in html_file:
            continue
        
        file_name = os.path.basename(html_file)
        schema_name = file_name.replace(".schema.html", "").replace("_", " ").title()
        
        index_content += f'                <li class="list-group-item"><a href="{file_name}">{schema_name}</a></li>\n'

    # Завершаем HTML документ
    index_content += """            </ul>
        </div>
        <div class="footer">
            <p>Документация автоматически сгенерирована из схем JSON. Последнее обновление: <span id="last-update"></span></p>
            <script>
                document.getElementById('last-update').textContent = new Date().toLocaleDateString();
            </script>
        </div>
    </div>
    <script src="schema_doc.min.js"></script>
</body>
</html>
"""

    # Записываем индексную страницу
    try:
        with open(os.path.join(docs_dir, "index.html"), "w", encoding='utf-8') as f:
            f.write(index_content)
        print("Индексная страница сгенерирована!")
        return True
    except Exception as e:
        print(f"Ошибка при создании индексной страницы: {e}")
        return False


def main() -> None:
    """
    Точка входа для консольной команды.
    """
    parser = argparse.ArgumentParser(
        description="Генератор индексной страницы для документации API"
    )
    parser.add_argument(
        "docs_dir", 
        nargs="?", 
        default="docs",
        help="Путь к директории с документацией (по умолчанию: docs)"
    )
    parser.add_argument(
        "project_name", 
        nargs="?", 
        default="Default Project",
        help="Имя проекта (по умолчанию: Default Project)"
    )
    
    args = parser.parse_args()
    success = generate_docs_index(args.docs_dir, args.project_name)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
