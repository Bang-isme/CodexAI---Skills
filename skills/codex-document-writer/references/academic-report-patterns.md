# Academic & University Report Patterns

Reference for writing academic reports, course assignments, thesis chapters, lab reports, and university deliverables — with Vietnamese support.

## Report Structure by Type

### Course Project Report (Báo cáo đồ án môn học)

```markdown
# <Tên đề tài>

## Trang bìa
- Trường: <tên trường>
- Khoa: <tên khoa>
- Môn học: <tên môn>
- Đề tài: <tên đề tài>
- GVHD: <tên giảng viên>
- Nhóm: <số nhóm>
- Thành viên:
  | STT | Họ và tên | MSSV | Vai trò | Đóng góp (%) |
  |-----|-----------|------|---------|---------------|
  | 1   | <tên>     | <id> | Leader  | <n>%          |
- Ngày nộp: <ngày>

## Mục lục
<Tự động hoặc thủ công>

## Danh mục hình ảnh
| Hình | Tên | Trang |
|------|-----|-------|
| Hình 1.1 | Sơ đồ kiến trúc tổng quan | <n> |

## Danh mục bảng biểu
| Bảng | Tên | Trang |
|------|-----|-------|
| Bảng 2.1 | So sánh công nghệ | <n> |

## Danh mục từ viết tắt
| Từ viết tắt | Ý nghĩa |
|-------------|---------|
| API | Application Programming Interface |
| SPA | Single Page Application |
```

### Chapter Templates

#### Chương 1: Giới thiệu

```markdown
## Chương 1: Giới thiệu

### 1.1. Đặt vấn đề
<Mô tả bối cảnh thực tế, pain point của người dùng, và lý do đề tài cần được thực hiện.>

### 1.2. Mục tiêu đề tài
**Mục tiêu tổng quát:**
<Một câu mô tả kết quả cuối cùng.>

**Mục tiêu cụ thể:**
1. <Mục tiêu đo lường được — ví dụ: "Xây dựng module quản lý người dùng với CRUD hoàn chỉnh">
2. <Mục tiêu đo lường được>
3. <Mục tiêu đo lường được>

### 1.3. Phạm vi đề tài

| Trong phạm vi | Ngoài phạm vi |
|----------------|----------------|
| <chức năng/module> | <chức năng bị loại> |

### 1.4. Phương pháp thực hiện
<Phương pháp phát triển: Agile/Scrum/Waterfall, lý do chọn.>

### 1.5. Cấu trúc báo cáo
- Chương 1: Giới thiệu
- Chương 2: Cơ sở lý thuyết
- Chương 3: Phân tích và thiết kế
- Chương 4: Hiện thực
- Chương 5: Kiểm thử
- Chương 6: Kết luận
```

#### Chương 2: Cơ sở lý thuyết

```markdown
## Chương 2: Cơ sở lý thuyết

### 2.1. Các công trình liên quan
<Tóm tắt 2-3 hệ thống/nghiên cứu tương tự, so sánh với đề tài hiện tại.>

| Hệ thống | Ưu điểm | Hạn chế | So với đề tài |
|-----------|---------|---------|---------------|
| <name> | <pro> | <con> | <how this project differs> |

### 2.2. Công nghệ sử dụng

#### 2.2.1. Frontend
<Mô tả công nghệ, phiên bản, lý do chọn.>

#### 2.2.2. Backend
<Mô tả công nghệ, phiên bản, lý do chọn.>

#### 2.2.3. Database
<Mô tả DBMS, lý do chọn, so sánh ngắn gọn với alternatives.>

| Tiêu chí | PostgreSQL | MySQL | MongoDB |
|----------|-----------|-------|---------|
| ACID | ✅ Full | ✅ Full | ⚠️ Partial |
| JSON support | ✅ JSONB | ⚠️ JSON | ✅ Native |
| Scalability | ✅ Good | ✅ Good | ✅ Excellent |

### 2.3. Kiến thức nền tảng
<Giải thích ngắn gọn các concept quan trọng: REST API, JWT, MVC, etc.>
```

#### Chương 3: Phân tích và thiết kế

```markdown
## Chương 3: Phân tích và thiết kế

### 3.1. Yêu cầu chức năng

| ID | Yêu cầu | Mô tả | Ưu tiên |
|----|---------|-------|---------|
| FR-01 | Đăng ký | Người dùng đăng ký bằng email | Cao |
| FR-02 | Đăng nhập | Xác thực bằng JWT | Cao |

### 3.2. Yêu cầu phi chức năng

| ID | Yêu cầu | Tiêu chí đo lường |
|----|---------|-------------------|
| NFR-01 | Hiệu suất | Thời gian phản hồi API < 500ms |
| NFR-02 | Bảo mật | Mã hóa mật khẩu bcrypt, HTTPS |

### 3.3. Use Case Diagram
<Mermaid hoặc hình ảnh>

### 3.4. Sơ đồ kiến trúc hệ thống
<Mermaid flowchart — architecture diagram>

### 3.5. Thiết kế cơ sở dữ liệu
#### 3.5.1. ERD
<Mermaid erDiagram>

#### 3.5.2. Mô tả bảng dữ liệu

**Bảng: users**
| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| id | UUID | PK | Mã người dùng |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email đăng nhập |

### 3.6. Thiết kế API

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| POST | /api/auth/register | Đăng ký | ❌ |
| POST | /api/auth/login | Đăng nhập | ❌ |
| GET | /api/users/me | Thông tin cá nhân | ✅ |

### 3.7. Thiết kế giao diện
<Wireframe hoặc mockup screenshots>
```

#### Chương 4: Hiện thực

```markdown
## Chương 4: Hiện thực

### 4.1. Môi trường phát triển

| Thành phần | Công cụ | Phiên bản |
|-----------|---------|-----------|
| OS | Windows 11 | 23H2 |
| IDE | VS Code | 1.9x |
| Runtime | Node.js | 20.x LTS |
| Database | PostgreSQL | 16.x |

### 4.2. Cấu trúc thư mục
<ASCII directory tree>

### 4.3. Hiện thực các chức năng chính

#### 4.3.1. Module xác thực
<Mô tả flow + code snippet quan trọng + screenshot>

**Luồng xử lý:**
<Mermaid sequence diagram>

**Code tiêu biểu:**
```javascript
// Chỉ show code quan trọng, không paste toàn bộ file
const login = async (email, password) => {
  const user = await User.findByEmail(email);
  if (!user || !await bcrypt.compare(password, user.password)) {
    throw new AppError('Invalid credentials', 401);
  }
  return jwt.sign({ id: user.id }, SECRET, { expiresIn: '24h' });
};
```

**Kết quả:**
<Screenshot giao diện hoặc API response>
```

#### Chương 5: Kiểm thử

```markdown
## Chương 5: Kiểm thử

### 5.1. Kế hoạch kiểm thử

| Loại | Công cụ | Phạm vi |
|------|---------|---------|
| Unit Test | Jest | Services, Utils |
| Integration Test | Supertest | API endpoints |
| E2E Test | Playwright | User flows |

### 5.2. Kết quả kiểm thử

#### 5.2.1. Unit Test

| Module | Tests | Pass | Fail | Coverage |
|--------|-------|------|------|----------|
| Auth Service | 12 | 12 | 0 | 95% |
| User Service | 8 | 8 | 0 | 88% |

#### 5.2.2. Test Cases

| TC-ID | Chức năng | Input | Expected | Actual | Kết quả |
|-------|-----------|-------|----------|--------|---------|
| TC-01 | Đăng ký | Email hợp lệ | 201 Created | 201 Created | ✅ Pass |
| TC-02 | Đăng ký | Email trùng | 409 Conflict | 409 Conflict | ✅ Pass |
| TC-03 | Đăng nhập | Sai mật khẩu | 401 Unauthorized | 401 Unauthorized | ✅ Pass |

### 5.3. Kiểm thử hiệu suất

| Endpoint | Concurrent Users | Avg Response | P95 | Error Rate |
|----------|-----------------|-------------|-----|-----------|
| GET /api/users | 100 | 45ms | 120ms | 0% |
| POST /api/orders | 50 | 180ms | 350ms | 0.1% |
```

#### Chương 6: Kết luận

```markdown
## Chương 6: Kết luận

### 6.1. Kết quả đạt được

| Mục tiêu | Kết quả | Đánh giá |
|----------|---------|----------|
| <mục tiêu 1> | <kết quả cụ thể> | ✅ Đạt / ⚠️ Đạt một phần / ❌ Chưa đạt |

### 6.2. Hạn chế
- <Hạn chế cụ thể và lý do.>

### 6.3. Hướng phát triển
- <Tính năng hoặc cải tiến cụ thể có thể thực hiện.>

## Tài liệu tham khảo

[1] <Tác giả>, "<Tiêu đề>", <Nhà xuất bản/Tạp chí>, <Năm>. [Online]. Available: <URL>
[2] <Tác giả>, <Tiêu đề>, <Nguồn>, <Năm>.
```

## Formatting Standards for Vietnamese Academic Documents

### Figure & Table Numbering
- Figures: `Hình <chapter>.<number>` — Ví dụ: Hình 3.2
- Tables: `Bảng <chapter>.<number>` — Ví dụ: Bảng 2.1
- Always place caption BELOW figures, ABOVE tables

### Citation Format
- In-text: `[1]` hoặc `(Nguyễn, 2024)`
- Bibliography: IEEE style hoặc APA — chọn một và dùng xuyên suốt

### Common Vietnamese Academic Phrases

| Context | Vietnamese |
|---------|-----------|
| "This chapter presents..." | "Chương này trình bày..." |
| "As shown in Figure X..." | "Như thể hiện ở Hình X..." |
| "The results indicate..." | "Kết quả cho thấy..." |
| "In summary..." | "Tóm lại..." |
| "Compared to..." | "So với..." |
| "The system consists of..." | "Hệ thống bao gồm..." |
| "The main contribution is..." | "Đóng góp chính là..." |

### Page Layout Guidelines
- Font: Times New Roman 13pt hoặc 14pt
- Line spacing: 1.5
- Margins: Top 3.5cm, Bottom 3cm, Left 3.5cm, Right 2cm
- Page numbers: Bottom center, bắt đầu từ trang nội dung
- Paragraph indent: 1.27cm (0.5 inch)
