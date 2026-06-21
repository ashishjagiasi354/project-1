# 🛡️ Biometric Protection AI

A full-stack, cloud-deployed Computer Vision application engineered to safeguard user privacy by automatically redacting sensitive biometric signatures from high-resolution digital media.

▶️ **[Live Web Application](https://biometric-protection.vercel.app/)**  
⚡ **Backend API Service:** Hosted on Render Cloud Infrastructure

---

## 🔍 The Privacy Challenge
With modern smartphone cameras shooting in ultra-high resolution, a casual "peace-sign" selfie or hand gesture now captures enough high-frequency skin-ridge detail to allow biometric fingerprint extraction and identity cloning. 

**Biometric Protection AI** systematically mitigates this vulnerability. The application dynamically parses uploaded media, isolates hand landmark structures using machine learning, and precisely overlays a localized Gaussian blur filter across tracked fingertip coordinates—effectively redacting unique biometric signatures while preserving the integrity of the surrounding image.

---

## 🛠️ System Architecture & Tech Stack

| Layer | Technology | Purpose / Role | Deployment |
| :--- | :--- | :--- | :--- |
| **Frontend** | `Next.js` (React) • `TypeScript` | Responsive UI, state management, & asynchronous file handling | **Vercel** |
| **Styles** | `Tailwind CSS` | Unified dark-theme dashboard architecture | — |
| **Backend** | `FastAPI` (Python) | High-performance, asynchronous RESTful API endpoints | **Render** (Linux) |
| **ML Engine**| `Google MediaPipe` | Real-time hand landmark and coordinate vector tracking | — |
| **Graphics** | `OpenCV` (`cv2`) | Multidimensional NumPy matrix operations & image processing | — |
| **DevSecOps**| `Git` • `GitHub` | Automated CI/CD pipeline triggers on production branch updates | — |

---

## 🚀 Key Engineering Challenges Overcome

* **Asynchronous Image Processing:** Managed the structural translation of multi-part form-data image streams into raw NumPy multi-dimensional arrays on the server, ensuring memory-efficient landmark mapping and minimal execution latency.
* **Network & Cross-Origin Security:** Hardened the backend API interface by implementing explicit Cross-Origin Resource Sharing (CORS) middlewares, strictly white-listing traffic exclusively originating from the production client domain.
* **Cloud Dependency Resolution:** Overcame platform-specific headless Linux environment constraints during cloud deployment by systematically configuring container-level system dependencies required for OpenCV and MediaPipe bindings.

---

## 💻 Local Development Setup

Follow these steps to run the complete decoupled ecosystem on your local machine:

### 1. Backend Service Setup (FastAPI)
```bash
# Navigate to backend directory and build a virtual environment
cd backend
python -m venv venv

# Activate the environment
# On Windows use: venv\Scripts\activate
source venv/bin/activate  

# Install dependencies and launch the reload server
pip install -r requirements.txt
uvicorn main:app --reload