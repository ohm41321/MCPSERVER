# MCP Multi-Server System

ระบบ MCP Server ที่มี 2 Servers/Ports แยกกัน โดยเชื่อมต่อกับฐานข้อมูล PostgreSQL สำหรับเก็บ Tools แยกสำหรับแต่ละ Server

## 🏗️ Architecture

ระบบประกอบด้วย:
- **MCP Server A** (Port 3001) - เซิร์ฟเวอร์หลักสำหรับเครื่องมือการเงิน
- **MCP Server B** (Port 3002) - เซิร์ฟเวอร์รองสำหรับเครื่องมือทั่วไป
- **PostgreSQL Database** - เก็บข้อมูล Tools แยกตาม Server
- **Tool Management System** - จัดการเครื่องมือแบบ Server-specific

## 📋 Features

### Server A (Port 3001) - Finance Tools
- `get_stock_price` - ดูราคาหุ้นปัจจุบัน
- `calculate_portfolio` - คำนวณมูลค่าพอร์ตการลงทุน
- `get_financial_news` - อ่านข่าวการเงินล่าสุด

### Server B (Port 3002) - Utility Tools
- `get_weather` - ดูข้อมูลสภาพอากาศ
- `get_time` - ดูเวลาปัจจุบันตามโซนเวลา
- `data_processor` - ประมวลผลข้อมูล
- `text_analyzer` - วิเคราะห์ข้อความ

## 🚀 การติดตั้งและใช้งาน

### 1. Prerequisites

```bash
# Python 3.8+
python --version

# PostgreSQL
# ตรวจสอบการเชื่อมต่อฐานข้อมูล
```

### 2. ติดตั้ง Dependencies

```bash
# ติดตั้ง Python packages
pip install -r requirements.txt

# หรือติดตั้งทีละตัว
pip install fastapi uvicorn psycopg2-binary sqlalchemy python-dotenv
```

### 3. กำหนดค่า Environment Variables

แก้ไขไฟล์ `.env`:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:%40Ohm230946@localhost/mcp_config

# MCP Server Configuration
PORT_A=3001
PORT_B=3002

# Server A Configuration
SERVER_A_NAME=server_a
SERVER_A_HOST=0.0.0.0

# Server B Configuration
SERVER_B_NAME=server_b
SERVER_B_HOST=0.0.0.0

# Development
DEBUG=true
LOG_LEVEL=INFO
```

### 4. เริ่มใช้งานระบบ

#### วิธีที่ 1: เริ่มทั้งสองเซิร์ฟเวอร์อัตโนมัติ

```bash
# เริ่มทั้งสองเซิร์ฟเวอร์พร้อมกัน
python -m app.main

# หรือ
python app/main.py
```

#### วิธีที่ 2: เริ่มเซิร์ฟเวอร์แยกกัน

```bash
# Terminal 1: เริ่ม Server A
python -m app.server_a

# Terminal 2: เริ่ม Server B
python -m app.server_b
```

## 🔗 API Endpoints

### Health Check

ตรวจสอบสถานะเซิร์ฟเวอร์:

```bash
# Server A
curl http://localhost:3001/health

# Server B
curl http://localhost:3002/health
```

Response:
```json
{
  "status": "healthy",
  "server": "Server A",
  "port": 3001,
  "database": "connected",
  "timestamp": "2025-10-15T04:24:19.506Z"
}
```

### Server Information

ดูข้อมูลเซิร์ฟเวอร์และเครื่องมือที่มี:

```bash
# Server A
curl http://localhost:3001/info

# Server B
curl http://localhost:3002/info
```

### List Tools

ดูรายการเครื่องมือทั้งหมด:

```bash
# Server A
curl http://localhost:3001/tools

# Server B
curl http://localhost:3002/tools
```

### Register New Tool

เพิ่มเครื่องมือใหม่:

```bash
curl -X POST http://localhost:3001/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_tool",
    "description": "Description of the new tool",
    "parameters": [
      {
        "name": "param1",
        "type": "string",
        "description": "Parameter description",
        "required": true
      }
    ]
  }'
```

### Execute Tool

เรียกใช้งานเครื่องมือ:

```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_stock_price",
    "arguments": {
      "operation": "execute",
      "symbol": "AAPL"
    }
  }'
```

## 🛠️ การพัฒนาและทดสอบ

### การเพิ่ม Tools ใหม่

1. เพิ่ม logic ในไฟล์ `server_a.py` หรือ `server_b.py`
2. ใน method `_execute_tool_logic()` เพิ่ม case สำหรับ tool ใหม่
3. เพิ่ม method handler สำหรับ tool นั้นๆ

ตัวอย่าง:

```python
elif tool['name'] == 'new_tool':
    return await self._handle_new_tool(operation, args)

async def _handle_new_tool(self, operation: str, args: Any) -> Dict[str, Any]:
    if operation == 'execute':
        return {
            'operation': 'new_tool',
            'result': 'ผลลัพธ์จาก tool ใหม่',
            'server': 'Server A'
        }
    else:
        raise ValueError(f"Unknown new_tool operation: {operation}")
```

### การทดสอบ

```bash
# ทดสอบ Health Check
curl http://localhost:3001/health
curl http://localhost:3002/health

# ทดสอบ List Tools
curl http://localhost:3001/tools
curl http://localhost:3002/tools

# ทดสอบ Execute Tool
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_stock_price",
    "arguments": {
      "operation": "execute",
      "symbol": "AAPL"
    }
  }'
```

## 📊 การตรวจสอบและ Monitoring

### Log Files

ระบบจะบันทึก logs ไว้ที่ console สามารถดูได้จาก terminal ที่รันเซิร์ฟเวอร์

### Database

ตรวจสอบข้อมูลในฐานข้อมูล:

```sql
-- ดูเซิร์ฟเวอร์ทั้งหมด
SELECT DISTINCT server_id FROM tools;

-- ดู tools ของ Server A
SELECT * FROM tools WHERE server_id LIKE '%server_a%';

-- ดู tools ของ Server B
SELECT * FROM tools WHERE server_id LIKE '%server_b%';

-- นับจำนวน tools ต่อเซิร์ฟเวอร์
SELECT server_id, COUNT(*) as tool_count
FROM tools
GROUP BY server_id;
```

## 🔧 การแก้ไขปัญหา

### ปัญหาทั่วไป

1. **Database Connection Error**
   - ตรวจสอบ DATABASE_URL ในไฟล์ .env
   - ตรวจสอบว่า PostgreSQL กำลังรันอยู่
   - ตรวจสอบ username/password

2. **Port Already in Use**
   - เปลี่ยน PORT_A หรือ PORT_B ในไฟล์ .env
   - ปิดโปรแกรมอื่นที่ใช้ port เดียวกัน

3. **Module Not Found**
   - ติดตั้ง dependencies ด้วย `pip install -r requirements.txt`

### Debug Mode

เปิด debug mode ในไฟล์ .env:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📈 การขยายระบบ

### เพิ่มเซิร์ฟเวอร์ใหม่

1. สร้างไฟล์ `server_c.py` ใหม่
2. เพิ่ม PORT_C ในไฟล์ .env
3. เพิ่ม server_name ใน database query
4. อัปเดต `main.py` เพื่อรันเซิร์ฟเวอร์ใหม่

### เพิ่มประเภท Tools ใหม่

1. เพิ่ม logic ในเซิร์ฟเวอร์ที่เกี่ยวข้อง
2. อัปเดต database schema ถ้าจำเป็น
3. ทดสอบการทำงาน

## 🔐 Security

- ใช้ HTTPS ใน production
- กำหนด CORS policy อย่างเหมาะสม
- ตรวจสอบ input validation
- ใช้ environment variables สำหรับข้อมูล sensitive

## 📝 License

MIT License - ดูไฟล์ LICENSE สำหรับรายละเอียด

## 🆘 Support

ถ้ามีปัญหาในการใช้งาน:
1. ตรวจสอบ logs ใน terminal
2. ทดสอบ database connection
3. ตรวจสอบ configuration ในไฟล์ .env
4. ลอง restart เซิร์ฟเวอร์ใหม่

---

**สร้างโดย:** MCP Server Team
**เวอร์ชัน:** 1.0.0
**อัปเดตล่าสุด:** 2025-10-15