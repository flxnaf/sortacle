# 🚀 SORTACLE QUICK START

## 1️⃣ SSH Into Servers

### Raspberry Pi (with X11)
```bash
ssh -Y ckitt@172.20.10.4
```

### Vultr Cloud Server
```bash
ssh root@155.138.195.172
```

---

## 2️⃣ Start Inference Server (Vultr)

```bash
cd /root/sortacle-inference/inference
source venv/bin/activate
python3 server.py
```

**Running on:** `http://155.138.195.172:8000`

---

## 3️⃣ Start Detector (Raspberry Pi)

```bash
cd ~/projects/sortacle/inference
source venv/bin/activate

# Set environment variables
export CLOUD_INFERENCE_URL="http://155.138.195.172:8000"
export DATABASE_URL="postgresql://sortacle_user:PASSWORD@155.138.195.172:5432/sortacle_db"

# Run detector with servo
python3 detector_ui_pro.py

# OR with mock servo (testing)
python3 detector_ui_pro.py --mock-servo
```

---

## 4️⃣ Pull Latest Code

### On Pi or Vultr
```bash
git pull origin main
```

### On Mac (push changes)
```bash
cd "/Users/felixfan/Coding Projects/sortacle/sortacle"
git add .
git commit -m "message"
git push
```

---

## 5️⃣ View Data

### On Pi (terminal)
```bash
python3 view_data.py
```

### From Website (database connection)
```
Host: 155.138.195.172
Port: 5432
Database: sortacle_db
User: sortacle_user
Password: [ASK FELIX]
```

---

## 🔧 Troubleshooting

### Test cloud inference
```bash
curl http://155.138.195.172:8000/
```

### Test database connection
```bash
psql "postgresql://sortacle_user:PASSWORD@155.138.195.172:5432/sortacle_db" -c "SELECT COUNT(*) FROM disposal_events;"
```

### Kill stuck process on Pi
```bash
pkill -f detector_ui_pro.py
```

### Check camera on Pi
```bash
libcamera-hello --timeout 5000
```

---

## 📊 Key Files

| File | Purpose |
|------|---------|
| `detector_ui_pro.py` | Main Pi detector (UI + servo + logging) |
| `server.py` | Vultr inference server (YOLO-World) |
| `cloud_data_logger.py` | Uploads data to PostgreSQL |
| `data_api.py` | REST API for website data access |
| `view_data.py` | View database stats in terminal |

---

## 🌐 Ports & Services

| Service | Port | Location |
|---------|------|----------|
| Inference API | 8000 | Vultr |
| Data API | 8001 | Pi or Vultr |
| PostgreSQL | 5432 | Vultr |

---

## 🎯 Demo Flow

1. Start Vultr inference server (port 8000)
2. Start Pi detector (with X11 window showing detections)
3. Place item in camera view
4. System detects → logs to cloud PostgreSQL → servo rotates
5. Website shows live stats from PostgreSQL

---

## ⚠️ Important IPs

- **Pi**: `172.20.10.4` (changes per network)
- **Vultr**: `155.138.195.172` (static)

---

## 📝 Notes

- Always activate venv before running Python scripts
- Set environment variables before running detector
- Pull latest code before each demo
- Use `--mock-servo` flag to test without servo hardware
