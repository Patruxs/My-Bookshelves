import json

books_to_add = [
  {
    'id': 'e02ea8cd7b5f',
    'title': 'OCP_17_Programmer_s_guide',
    'category': 'Computer Science Fundamentals',
    'topic': 'Programming Languages',
    'file_path': 'Books/1_Computer_Science_Fundamentals/Programming_Languages/Java/OCP_17_Programmer_s_guide.pdf',
    'cover': 'assets/covers/OCP_17_Programmer_s_guide.webp',
    'format': 'pdf',
    'description': 'The Oracle Certified Professional (OCP) Java SE 17 certification is a rigorous exam that validates a developer\'s deep understanding of the Java language. Passing this exam requires more than just everyday programming experience; it demands comprehensive knowledge of edge cases, new language features, and core API intricacies.\n\nThis Programmer\'s Guide is a complete study resource tailored specifically for the Java SE 17 Developer exam. It walks through all the essential exam objectives, providing clear explanations, code examples, and practice questions to ensure thorough preparation for the actual certification test.\n\n• Master new Java 17 features including records, sealed classes, pattern matching, and text blocks\n• Deep dive into object-oriented concepts, generics, and the Java Collections Framework\n• Understand advanced concurrency mechanisms and the java.util.concurrent package\n• Learn the nuances of Java I/O (NIO.2) and serialization\n• Practice with exam-style questions to identify weak areas and solidify core knowledge'
  },
  {
    'id': '4df3d728fadb',
    'title': 'Database_Indexing_Nhung_Dieu_Developer_Can_Biet',
    'category': 'Software Engineering Disciplines',
    'topic': 'Database',
    'file_path': 'Books/2_Software_Engineering_Disciplines/Database/Database_Indexing_Nhung_Dieu_Developer_Can_Biet.epub',
    'cover': 'assets/covers/Database_Indexing_Nhung_Dieu_Developer_Can_Biet.webp',
    'format': 'epub',
    'description': 'Hiệu năng cơ sở dữ liệu là yếu tố then chốt quyết định tốc độ và độ ổn định của ứng dụng web. Một trong những nguyên nhân phổ biến nhất gây ra tình trạng chậm chạp của hệ thống là do thiếu kiến thức về cách lập chỉ mục (indexing) khi truy vấn dữ liệu.\n\nCuốn sách "Database Indexing & Những Điều Developer Cần Biết" cung cấp những kiến thức thực tiễn và chuyên sâu về cách thức hoạt động của Index trong cơ sở dữ liệu. Từ đó giúp lập trình viên hiểu rõ bản chất và cách áp dụng index hiệu quả để tối ưu hóa hiệu suất truy vấn.\n\n• Hiểu cơ chế hoạt động của B-Tree index và Hash index trong các hệ quản trị cơ sở dữ liệu\n• Cách phân tích Execution Plan để phát hiện các truy vấn thiếu tối ưu\n• Kỹ thuật tạo composite index và các nguyên tắc Leftmost Prefix Rule\n• Những trường hợp không nên sử dụng index để tránh làm chậm thao tác ghi dữ liệu\n• Các mẹo tối ưu hóa câu lệnh SQL kết hợp với index hiệu quả'
  },
  {
    'id': '566ef9a5de12',
    'title': 'Database_Indexing_Nhung_Dieu_Developer_Can_Biet',
    'category': 'Software Engineering Disciplines',
    'topic': 'Database',
    'file_path': 'Books/2_Software_Engineering_Disciplines/Database/Database_Indexing_Nhung_Dieu_Developer_Can_Biet.pdf',
    'cover': 'assets/covers/Database_Indexing_Nhung_Dieu_Developer_Can_Biet.webp',
    'format': 'pdf',
    'description': 'Hiệu năng cơ sở dữ liệu là yếu tố then chốt quyết định tốc độ và độ ổn định của ứng dụng web. Một trong những nguyên nhân phổ biến nhất gây ra tình trạng chậm chạp của hệ thống là do thiếu kiến thức về cách lập chỉ mục (indexing) khi truy vấn dữ liệu.\n\nCuốn sách "Database Indexing & Những Điều Developer Cần Biết" cung cấp những kiến thức thực tiễn và chuyên sâu về cách thức hoạt động của Index trong cơ sở dữ liệu. Từ đó giúp lập trình viên hiểu rõ bản chất và cách áp dụng index hiệu quả để tối ưu hóa hiệu suất truy vấn.\n\n• Hiểu cơ chế hoạt động của B-Tree index và Hash index trong các hệ quản trị cơ sở dữ liệu\n• Cách phân tích Execution Plan để phát hiện các truy vấn thiếu tối ưu\n• Kỹ thuật tạo composite index và các nguyên tắc Leftmost Prefix Rule\n• Những trường hợp không nên sử dụng index để tránh làm chậm thao tác ghi dữ liệu\n• Các mẹo tối ưu hóa câu lệnh SQL kết hợp với index hiệu quả'
  }
]

with open('site/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

existing_paths = {b['file_path'] for b in data}
added_count = 0
for b in books_to_add:
    if b['file_path'] not in existing_paths:
        data.append(b)
        added_count += 1

with open('site/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Successfully added {added_count} books to data.json')
