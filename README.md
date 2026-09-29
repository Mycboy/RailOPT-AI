# OptRail-AI 🚆🤖

**Intelligent AI-Powered Railway Maintenance Scheduling & What-If Simulation Engine**

OptRail-AI is an end-to-end decision support platform designed for Indian Railways. It integrates Operations Research (Google OR-Tools CP-SAT constraint programming) with real-time operational constraints, Role-Based Access Control (RBAC), and interactive scenario simulations to schedule railway maintenance blocks without disrupting high-priority train movements.

---

## 🌟 Key Features

- **Constraint Optimization Engine**: Powered by Google OR-Tools CP-SAT to resolve track possession window conflicts, resource bottlenecks, and safety buffers.
- **Role-Based Access Control (RBAC)**: Custom JWT authentication supporting Chief Controllers (Rajesh Kumar), Electrical/OHE Engineers (Arun Verma), Permanent Way/Engineering Supervisors (Priya Sharma), and Safety Officers.
- **Dynamic What-If Simulation Engine**: Simulate unexpected track failures, speed restrictions (TSR), emergency blocks, and priority train delays.
- **Interactive Visualization**: Network corridor map, Gantt chart timeline, conflict radar, and operations cost breakdown.

---

## 🚀 Deploying Backend on Render

The repository is pre-configured for **1-click deployment on Render** using `render.yaml`, `Procfile`, and `main.py`.

### Option A: Using Render Blueprint (Recommended)
1. In your [Render Dashboard](https://dashboard.render.com/), click **New +** > **Blueprint**.
2. Connect your GitHub repository (`RailOPT-AI`).
3. Render will automatically detect `render.yaml` and configure:
   - **Runtime**: Python 3.11.9
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Apply**.

---

### Option B: Manual Web Service Setup on Render
If setting up as an individual Web Service:
1. Click **New +** > **Web Service**.
2. Select your repository: `https://github.com/Mycboy/RailOPT-AI.git`.
3. Set the following parameters:
   | Setting | Value |
   | :--- | :--- |
   | **Name** | `optrail-ai-backend` |
   | **Region** | Singapore / Frankfurt / Oregon (nearest to you) |
   | **Branch** | `main` |
   | **Root Directory** | *(leave blank / root)* |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

4. Under **Environment Variables**, add:
   - `PYTHON_VERSION` = `3.11.9`

5. Click **Create Web Service**. Render will install requirements and bind to `$PORT` automatically.

---

## 🌐 Deploying Frontend (Vercel / Netlify / Render)

When deploying the frontend in `frontend/`:
1. **Root Directory**: `frontend`
2. **Build Command**: `npm run build`
3. **Output Directory**: `dist`
4. **Environment Variables**:
   - `VITE_API_BASE_URL` = `https://<your-render-backend-url>.onrender.com` (your deployed Render URL)

---

## 💻 Local Development Setup

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Mycboy/RailOPT-AI.git
cd RailOPT-AI

# Create virtual environment
python -m venv .venv
# Activate on Windows:
.\.venv\Scripts\activate
# Activate on Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend API server
uvicorn main:app --reload --port 8000
```
API docs will be available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
