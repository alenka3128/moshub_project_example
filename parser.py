def read_file(file_path):
    if file_path.endswith('.txt'):
        # Для текстовых файлов читаем всё сразу или построчно
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()  # Возвращает список строк
    elif file_path.endswith('.csv'):
        # Для CSV используется модуль csv — корректно обрабатывает запятые в кавычках
        import csv
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            return [row for row in reader]  # Возвращает список списков (каждая строка — список полей)
    else:
        raise ValueError("Неподдерживаемый тип файла. Разрешены только .txt и .csv")