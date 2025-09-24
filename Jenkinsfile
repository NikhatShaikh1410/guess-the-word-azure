// Jenkinsfile (Declarative Pipeline)

pipeline {
    agent any
    environment {
        // Project-specific configuration (customize these)
        ACR_NAME             = 'acrwordgamedemo' // Your unique ACR name
        CONTAINER_APP_NAME   = 'app-wordgame'
        TF_STATE_RG          = 'rg-tfstate' // RG for Terraform remote state
        TF_STATE_STORAGE     = 'sttfstateguessword' // Unique storage account for TF state

        IMAGE_TAG            = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
    }
    stages {

        // Stage: Install dependencies and run checks
        stage('Lint & Test') {
            steps {
                script {
                    echo "--- Starting Linting and Unit Tests ---"
                    // Use a temporary Python virtual environment for clean dependency management
                    sh 'python -m venv .venv'
                    sh '.venv/bin/pip install -r web/requirements.txt'
                    sh '.venv/bin/pip install flake8 pytest'
                    
                    echo "Running flake8 linter..."
                    sh '.venv/bin/flake8 web/'

                    echo "Running pytest..."
                    sh '.venv/bin/pytest web/tests/'
                }
            }
        }
        stage('Build & Security Scan') {
            steps {
                script {
                    echo "--- Building Docker Image: ${ACR_NAME}.azurecr.io/${CONTAINER_APP_NAME}:${IMAGE_TAG} ---"
                    sh "docker build -t ${ACR_NAME}.azurecr.io/${CONTAINER_APP_NAME}:${IMAGE_TAG} -f web/Dockerfile ./web"

                    echo "--- Scanning image for vulnerabilities with Trivy ---"
                    
                    sh "docker run --rm aquasec/trivy:latest image --exit-code 1 --severity HIGH,CRITICAL ${ACR_NAME}.azurecr.io/${CONTAINER_APP_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Push to ACR') {
            steps {
                echo "--- Pushing image to Azure Container Registry ---"
                // Use the 'ACR_CREDENTIALS' configured in Jenkins
                withCredentials([usernamePassword(credentialsId: 'ACR_CREDENTIALS', usernameVariable: 'ACR_USERNAME', passwordVariable: 'ACR_PASSWORD')]) {
                    sh "docker login ${ACR_NAME}.azurecr.io -u ${ACR_USERNAME} -p ${ACR_PASSWORD}"
                    sh "docker push ${ACR_NAME}.azurecr.io/${CONTAINER_APP_NAME}:${IMAGE_TAG}"
                }
            }
        }

        
        stage('Deploy to Staging') {
            steps {
                echo "--- Deploying to Staging Environment ---"
                withCredentials([azureServicePrincipal('AZURE_CREDENTIALS')]) {
                    sh 'az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID'
                    
                    dir('terraform') {
                        // Initialize Terraform with the remote backend configuration
                        sh """
                        terraform init -reconfigure \\
                            -backend-config="resource_group_name=${TF_STATE_RG}" \\
                            -backend-config="storage_account_name=${TF_STATE_STORAGE}" \\
                            -backend-config="container_name=tfstate" \\
                            -backend-config="key=wordgame.staging.tfstate"
                        """
                        sh 'terraform workspace select staging || terraform workspace new staging'
                        sh "terraform apply -auto-approve -var='docker_image_tag=${IMAGE_TAG}'"
                    }
                }
            }
        }
        stage('Smoke Test Staging') {
            steps {
                script {
                    echo "--- Running Smoke Test on Staging ---"
                    // Get the application URL from Terraform output
                    def appUrl = sh(returnStdout: true, script: "cd terraform && terraform output -raw container_app_url").trim()
                    
                    echo "Testing URL: ${appUrl}/api/health"
                    sh "curl --fail --silent --show-error ${appUrl}/api/health"
                }
            }
        }

        stage('Approval & Deploy to Production') {
            steps {
                input message: 'Deploy to Production?', ok: 'Yes, Deploy!'

                echo "--- Deploying to Production Environment ---"
                withCredentials([azureServicePrincipal('AZURE_CREDENTIALS')]) {
                    sh 'az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID'

                    dir('terraform') {
                        sh """
                        terraform init -reconfigure \\
                            -backend-config="resource_group_name=${TF_STATE_RG}" \\
                            -backend-config="storage_account_name=${TF_STATE_STORAGE}" \\
                            -backend-config="container_name=tfstate" \\
                            -backend-config="key=wordgame.production.tfstate"
                        """
                        sh 'terraform workspace select production || terraform workspace new production'
                        
                        // IMPORTANT: Deploy the SAME image tag that was tested in staging
                        sh "terraform apply -auto-approve -var='docker_image_tag=${IMAGE_TAG}'"
                    }
                }
            }
        }
    }

   
    post {
        always {
            echo "--- Pipeline Finished. Cleaning up... ---"
            sh "docker logout ${ACR_NAME}.azurecr.io"

            cleanWs()
        }
    }
}