# Guess the Word - Azure DevOps Project

This project is a complete, production-grade deployment of a "Guess the Word" web game on Microsoft Azure. It demonstrates modern DevOps practices using Terraform for infrastructure and Jenkins for a complete CI/CD pipeline.

---

## 🚀 Tech Stack & Architecture

* **Frontend**: HTML, CSS, Vanilla JavaScript
* **Backend**: Python, Flask
* **Database**: Azure Database for PostgreSQL (Flexible Server)
* **Cloud Platform**: Microsoft Azure
* **Containerization**: Docker
* **IaC**: Terraform (with remote state and workspaces)
* **CI/CD**: **Jenkins**
* **Security**: Azure Managed Identity for passwordless DB access, Trivy for vulnerability scanning.

### Architecture Diagram

```mermaid
graph TD
    A[Developer] -- git push --> B{GitHub};
    B -- webhook --> C[Jenkins Controller];
    C -- triggers build on --> JenkinsAgent[Jenkins Agent];
    JenkinsAgent -- 1. Lint & Test --> JenkinsAgent;
    JenkinsAgent -- 2. Build & Scan Image --> JenkinsAgent;
    JenkinsAgent -- 3. Push Image --> D[Azure Container Registry];
    JenkinsAgent -- 4. Deploy --> E[Terraform];
    E -- provisions --> F[Azure Container App];
    E -- provisions --> G[Azure PostgreSQL];
    F -- pulls image from --> D;
    F -- connects via Managed Identity --> G;
    H[User] -- HTTPS --> F;

Markdown

# Guess the Word - Azure DevOps Project

This project is a complete, production-grade deployment of a "Guess the Word" web game on Microsoft Azure. It demonstrates modern DevOps practices using Terraform for infrastructure and Jenkins for a complete CI/CD pipeline.

---

## 🚀 Tech Stack & Architecture

* **Frontend**: HTML, CSS, Vanilla JavaScript
* **Backend**: Python, Flask
* **Database**: Azure Database for PostgreSQL (Flexible Server)
* **Cloud Platform**: Microsoft Azure
* **Containerization**: Docker
* **IaC**: Terraform (with remote state and workspaces)
* **CI/CD**: **Jenkins**
* **Security**: Azure Managed Identity for passwordless DB access, Trivy for vulnerability scanning.

### Architecture Diagram

```mermaid
graph TD
    A[Developer] -- git push --> B{GitHub};
    B -- webhook --> C[Jenkins Controller];
    C -- triggers build on --> JenkinsAgent[Jenkins Agent];
    JenkinsAgent -- 1. Lint & Test --> JenkinsAgent;
    JenkinsAgent -- 2. Build & Scan Image --> JenkinsAgent;
    JenkinsAgent -- 3. Push Image --> D[Azure Container Registry];
    JenkinsAgent -- 4. Deploy --> E[Terraform];
    E -- provisions --> F[Azure Container App];
    E -- provisions --> G[Azure PostgreSQL];
    F -- pulls image from --> D;
    F -- connects via Managed Identity --> G;
    H[User] -- HTTPS --> F;
🔧 Local Development Setup
Follow these steps to run the application on your local machine.

Prerequisites:

Python 3.9+

Docker & Docker Compose

Git

Steps:

Clone the repository:

Bash

git clone [https://github.com/YOUR_USERNAME/guess-the-word-azure.git](https://github.com/YOUR_USERNAME/guess-the-word-azure.git)
cd guess-the-word-azure
Start the local database:

Bash

docker-compose up -d
Create and activate a Python virtual environment:

Windows (PowerShell):

PowerShell

python -m venv .venv
.\.venv\Scripts\Activate.ps1
macOS / Linux:

Bash

python -m venv .venv
source .venv/bin/activate
Install dependencies using pip-tools:

Bash

pip install pip-tools
cd web
pip-compile requirements.in
pip install -r requirements.txt
cd ..
Run the application:
Create a .env file in the root directory for local secrets and run the app.

Bash

flask run
The application will be available at http://127.0.0.1:5000.

⚙️ CI/CD Pipeline (Jenkins)
This project uses a Jenkinsfile to define an automated CI/CD pipeline that builds, tests, and deploys the application to Azure.

Step 1: Jenkins Server Prerequisites
Your Jenkins environment must be configured with the following:

Required Plugins:

Pipeline

Git

Docker Pipeline

Credentials Binding

Azure Credentials

Agent Configuration:
The Jenkins agent(s) that will run this pipeline must have the following tools installed and available in the system's PATH:

Docker

Python 3.9+ & venv

Azure CLI

Terraform

Step 2: Configure Jenkins Credentials
In your Jenkins dashboard (Manage Jenkins > Credentials), you must create two sets of credentials:

Azure Service Principal Credentials:

Type: Azure Service Principal

ID: AZURE_CREDENTIALS

Details: Fill in your Subscription ID, Client ID, Client Secret, and Tenant ID.

Azure Container Registry (ACR) Credentials:

Type: Username with password

ID: ACR_CREDENTIALS

Details: Provide the credentials (e.g., a Service Principal with AcrPush role) for your container registry.

Step 3: Set Up Terraform Remote State Backend
The pipeline stores Terraform's state file in a remote Azure Storage Account. You must create this once.

Log in to Azure CLI:

Bash

az login
Create the resources: (Replace placeholders with your unique names)

Bash

# Variables
RESOURCE_GROUP_NAME="rg-tfstate"
STORAGE_ACCOUNT_NAME="sttfstateguessword" # MUST BE GLOBALLY UNIQUE
LOCATION="eastus"

# Create Resource Group
az group create --name $RESOURCE_GROUP_NAME --location $LOCATION

# Create Storage Account
az storage account create --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP_NAME --sku Standard_LRS

# Create Storage Container
az storage container create --name tfstate --account-name $STORAGE_ACCOUNT_NAME
Step 4: Create the Jenkins Pipeline Job
In Jenkins, click New Item.

Enter a name for your pipeline (e.g., guess-the-word-azure) and select Pipeline. Click OK.

In the configuration page, scroll down to the Pipeline section.

Select Pipeline script from SCM.

SCM: Choose Git.

Repository URL: Enter the URL of your forked GitHub repository.

Branch Specifier: Leave as */main.

Script Path: Ensure it is set to Jenkinsfile (the default).

Click Save.

You can now run the pipeline by clicking Build Now. The pipeline will execute all stages defined in the Jenkinsfile.

💰 Cost Management
This project uses Azure resources that incur costs. To manage them:

Use Low-Cost SKUs: The Terraform configuration uses B_Standard_B1ms for PostgreSQL and the lowest tier for Container Apps, suitable for development.

Set Up Budgets: It is highly recommended to set up an Azure Budget for the project's resource groups (rg-wordgame-staging, rg-wordgame-production) to get alerts if costs exceed a certain threshold.

Clean Up: To avoid ongoing charges, you can destroy all provisioned resources using Terraform from a machine with access to the state file.
