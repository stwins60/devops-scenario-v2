pipeline {

    agent any

    environment {
        IMAGE_NAME = "idrisniyi94/devops-scenario-v2"
        BRANCH_NAME = "${GIT_BRANCH.split('/')[1]}"
        IMAGE_TAG = "v.0.0.${env.BUILD_NUMBER}"
        DOCKERHUB_CREDENTIALS = credentials("9dbed14c-6cd8-4f0e-b1fa-2548be3f0c6c")
    }

    stages {
        stage("Docker Login") {
            steps {
                sh "echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin"
                echo "Login Successful"
            }
        }
        stage("Docker Build") {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }
        stage("Scan Docker Image with Trivy") {
            steps {
                script {
                    sh '''
                    if [ ! -f html.tpl ]; then
                    curl -sSL -o html.tpl https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/html.tpl
                    fi

                    docker run --rm \
                    -v $(pwd):/workspace \
                    -w /workspace \
                    aquasec/trivy:latest \
                    image ${IMAGE_NAME}:${IMAGE_TAG} \
                    --format template \
                    --template "@html.tpl" \
                    --output trivy-report.html
                    '''
                }
            }
        }
        stage("Publish Trivy Scanned Image Report") {
            steps {
                publishHTML([allowMissing: false, alwaysLinkToLastBuild: true, keepAll: true, reportDir: '.', reportFiles: 'trivy-report.html', reportName: 'Trivy Scanned Image Vulnerability Report'])
            }
        }
        stage("Docker Push") {
            steps {
                script {
                    def imageName = "${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${imageName}"
                }
            }
        }
        stage("Update Namespace and Image Name") {
            steps {
                script {
                    dir('./k8s') {
                        if (env.BRANCH_NAME == 'dev') {
                            sh "sed -i 's/NAMESPACE/dev/g' deploy.yaml"
                            sh "sed -i 's/NAMESPACE/dev/g' svc.yaml"
                            sh "sed -i 's|IMAGE_NAME${IMAGE_NAME}:${IMAGE_TAG}|g' deploy.yaml"
                        } else if (env.BRANCH_NAME == 'prod') {
                            sh "sed -i 's/NAMESPACE/prod/g' deploy.yaml"
                            sh "sed -i 's/NAMESPACE/prod/g' svc.yaml"
                            sh "sed -i 's|IMAGE_NAME${IMAGE_NAME}:${IMAGE_TAG}|g' deploy.yaml"
                        }
                    }
                }
            }
        }
        stage("Deploy to K8s") {
            steps {
                script {
                    dir('./k8s') {
                        withCredentials([file(credentialsId: '783ec1bf-41ab-4ffe-af3c-e408e701d542', variable: 'KUBECONFIG')]) {
                            sh "kubectl apply -f ."
                        }
                    }
                }
            }
        }
    }

}