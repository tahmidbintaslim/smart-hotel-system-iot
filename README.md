# Smart Hotel Management System

## Overview

The **Smart Hotel Management System** is a simplified IoT solution for managing hotel rooms. It includes:

- Simulated IoT devices for hotel rooms.
- Real-time data processing and energy management.
- A chatbot interface to enhance the guest experience.

This system is containerized using Docker, which means you don’t need any coding knowledge to deploy it. Just follow the steps below to get started!

---

## Supported Platforms

This guide provides instructions for the following platforms:

- **Windows**
- **Linux**
- **macOS**

---

## Prerequisites

Before deploying the system, make sure you have the following installed:

1. **Docker**:

   - Download and install from [https://www.docker.com/](https://www.docker.com/).
   - Follow the platform-specific installation guide:
     - [Windows Installation Guide](https://docs.docker.com/desktop/install/windows-install/)
     - [Linux Installation Guide](https://docs.docker.com/desktop/install/linux-install/)
     - [macOS Installation Guide](https://docs.docker.com/desktop/install/mac-install/)

2. **Git**:

   - Download and install from [https://git-scm.com/](https://git-scm.com/).

3. **Docker Compose**:
   - Comes pre-installed with Docker Desktop for Windows and macOS.
   - For Linux, install it manually by following [this guide](https://docs.docker.com/compose/install/).

---

## How to Deploy the System

### **Step 1: Clone the Repository**

First, download the project code to your computer using Git.

1. Open your terminal:

   - On **Windows**: Use Command Prompt, PowerShell, or Git Bash.
   - On **Linux/macOS**: Use your default terminal.

2. Run the following command to clone the project repository:

   ```bash
   git clone https://github.com/your-repository/smart-hotel-management.git
   ```

3. Navigate into the project folder:
   ```bash
   cd smart-hotel-management
   ```

---

### **Step 2: Make the Deployment Script Executable (Linux/macOS Only)**

On Linux or macOS, you need to make the deployment script executable. Run the following command:

```bash
chmod +x ./scripts/deploy.sh
```

On Windows, you can skip this step.

---

### **Step 3: Deploy the System**

To deploy the system, run the deployment script:

1. On **Linux/macOS**:

   ```bash
   ./scripts/deploy.sh start
   ```

2. On **Windows** (using Command Prompt or PowerShell):
   ```bash
   bash ./scripts/deploy.sh start
   ```

---

### **Step 4: Access the Services**

Once the system is deployed, you can access the following services in your browser:

1. **Frontend Chatbot**:

   - URL: [http://localhost:7860](http://localhost:7860)
   - Interact with your smart room by typing commands like:
     ```
     101 What is the current temperature?
     ```

2. **Backend API (Optional)**:
   - URL: [http://localhost:8000/docs](http://localhost:8000/docs)
   - This is the backend API documentation for developers.

---

## How to Manage the System

### **Start the System**

If the system is not running, start it with:

```bash
./scripts/deploy.sh start
```

### **Stop the System**

To stop the system, run:

```bash
./scripts/deploy.sh stop
```

### **Restart the System**

To restart the system, run:

```bash
./scripts/deploy.sh restart
```

---

## How It Works

The system consists of the following components:

1. **IoT Device Simulation**:
   - Simulates sensors that provide data like temperature, humidity, and room occupancy.
2. **Backend Processing**:
   - Analyzes sensor data, detects room occupancy, and manages energy usage.
3. **Frontend Chatbot**:
   - A simple chatbot interface for hotel guests to interact with their room devices (e.g., turning on lights or adjusting the AC).
4. **Database**:
   - Stores sensor data for real-time and historical analysis.

---

## Troubleshooting

### **Common Errors**

#### **1. Error: Docker is not installed**

- Solution: Install Docker by following the official guide: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/).

#### **2. Error: Room data not found**

- Solution: Ensure mock data is generated for the room by accessing:
  - [http://localhost:8000/life-being/101](http://localhost:8000/life-being/101)
  - [http://localhost:8000/iaq/101](http://localhost:8000/iaq/101)

#### **3. Error: Unauthorized. Access token is missing**

- Solution: Ensure your Azure API Key and Endpoint are correctly set in the deployment script. If needed, regenerate the API key in your Azure portal.

#### **4. Error: Deployment script permission denied**

- Solution: On Linux/macOS, make the script executable:
  ```bash
  chmod +x ./scripts/deploy.sh
  ```

---

## FAQs

### **Q: Do I need coding knowledge to use this system?**

No, you only need to follow the instructions in this guide. The deployment script handles everything for you.

### **Q: How do I verify if the system is running?**

Open your browser and visit:

- Frontend: [http://localhost:7860](http://localhost:7860)
- Backend: [http://localhost:8000/docs](http://localhost:8000/docs)

### **Q: How do I reset the system?**

Stop the system and then start it again:

```bash
./scripts/deploy.sh stop
./scripts/deploy.sh start
```

---

## Project Structure

Here’s a quick overview of the project structure:

```
smart-hotel-management/
├── backend/                # Backend code
│   ├── agents/             # Data fetcher, logger, and occupancy detector
│   ├── devices/            # IoT device simulation
│   └── api/                # API routes
├── frontend/               # Chatbot interface
│   └── chatbot.py
├── scripts/                # Deployment scripts
│   └── deploy.sh
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---
