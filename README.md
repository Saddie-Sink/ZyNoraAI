# Zynora ML — AI Architectural & Generative Design Platform

Zynora is an intelligent architectural design platform that generates optimized, culturally attuned residential floor plans, 3D parametric structures, and photorealistic architectural visualizations using machine learning and geometric optimization.

---

## 🏛️ Key Features

- **Automated Floor Plan Generation**: Graph Neural Network (GNN) and spatial optimization for room adjacency, circulation, and boundary constraints.
- **Indian Housing Typology & Vastu Compliance**:
  - Unsupervised clustering (K-Means) trained on Indian residential housing datasets.
  - Vastu Shastra rules engine evaluating orientation, elemental alignment (Agni, Ishanya, etc.), and spatial balance.
- **Quality & Cost Estimation**: Random Forest regression models estimating construction quality, viability, and area metrics.
- **Interactive 3D Visualization**: Real-time 3D model generation and exploration powered by Three.js in the browser.
- **Blender ArchViz Pipeline**: Automated Python-driven Blender rendering for multi-angle photorealistic renders.
- **Pareto Optimal Selection**: Multi-objective candidate ranking balancing cost, spatial efficiency, and regulatory compliance.

---

## 🛠️ Architecture & Tech Stack

### Frontend
- **Framework**: React 19 + Vite
- **3D Graphics**: Three.js
- **Routing**: React Router DOM v6
- **Styling**: Modern CSS variables & responsive layout

### Backend & Machine Learning
- **API Engine**: FastAPI + Uvicorn
- **ML & Geometry**:
  - PyTorch & PyTorch Geometric (GNN Layout generation & 3D extrusion)
  - Scikit-Learn & Joblib (Clustering & Quality Regressor)
  - Shapely, NetworkX, SciPy, NumPy (Geometric polygon operations & topological room graphs)
- **Dataset Integration**: Bengaluru Housing Dataset & Structured3D spatial layouts

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python run_backend.py
```
*Backend runs on `http://localhost:8000` (API documentation available at `/docs`).*

### 2. Frontend Setup

```bash
# In the root directory:
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 📂 Repository Structure

```
zynora-ml/
├── backend/
│   ├── app/             # FastAPI routes, ML engines, geometry & archviz
│   ├── data/            # Datasets (Bengaluru housing benchmarks)
│   ├── models/          # Trained GNN & ML model checkpoints
│   ├── tests/           # Backend unit and integration tests
│   ├── training/        # GNN and extrusion training pipelines & notebooks
│   └── requirements.txt # Python dependencies
├── public/              # Static assets and 3D architectural renders
├── src/                 # React frontend (components, pages, services, 3D viewer)
├── package.json
└── vite.config.js
```

---

## 📄 License

This project is licensed under the MIT License.
