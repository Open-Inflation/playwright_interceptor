import pytest
import os
import tempfile
from standard_open_inflation_package.utils.docs_generator import generate_docs_index


def test_generate_docs_index_with_html_files():
    """Тестирует генерацию индексной страницы с HTML файлами."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем тестовые HTML файлы
        test_files = [
            "schema1.schema.html",
            "schema2.schema.html", 
            "another_schema.schema.html"
        ]
        
        for file_name in test_files:
            with open(os.path.join(temp_dir, file_name), "w") as f:
                f.write("<html><body>Test content</body></html>")
        
        # Генерируем индексную страницу
        result = generate_docs_index(temp_dir, "TEST_PROJECT_API")
        
        assert result is True
        
        # Проверяем, что индексная страница создана
        index_path = os.path.join(temp_dir, "index.html")
        assert os.path.exists(index_path)
        
        # Проверяем содержимое индексной страницы
        with open(index_path, "r", encoding='utf-8') as f:
            content = f.read()

        assert "TEST_PROJECT_API / Response API Documentation" in content
        assert "Schema1" in content
        assert "Schema2" in content
        assert "Another Schema" in content


def test_generate_docs_index_empty_directory():
    """Тестирует генерацию индексной страницы в пустой директории."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = generate_docs_index(temp_dir, "TEST_PROJECT_API")
        
        assert result is True
        
        # Проверяем, что индексная страница создана
        index_path = os.path.join(temp_dir, "index.html")
        assert os.path.exists(index_path)
        
        # Проверяем, что в содержимом нет ссылок на схемы
        with open(index_path, "r", encoding='utf-8') as f:
            content = f.read()
            
        assert "TEST_PROJECT_API / Response API Documentation" in content
        assert content.count('<li class="list-group-item">') == 0


def test_generate_docs_index_nonexistent_directory():
    """Тестирует обработку несуществующей директории."""
    result = generate_docs_index("/nonexistent/directory")
    assert result is False


def test_index_html_ignored():
    """Тестирует что существующий index.html игнорируется при создании списка схем."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем существующий index.html и схему
        with open(os.path.join(temp_dir, "index.html"), "w") as f:
            f.write("<html><body>Old index</body></html>")
            
        with open(os.path.join(temp_dir, "test.schema.html"), "w") as f:
            f.write("<html><body>Test schema</body></html>")
        
        result = generate_docs_index(temp_dir)
        
        assert result is True
        
        # Проверяем, что в новом индексе есть только одна схема (test.schema.html)
        with open(os.path.join(temp_dir, "index.html"), "r", encoding='utf-8') as f:
            content = f.read()
            
        assert content.count('<li class="list-group-item">') == 1
        assert "Test" in content
