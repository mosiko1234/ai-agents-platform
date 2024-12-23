#!/bin/bash
# scripts/deploy.sh

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    COLOR=$1
    TEXT=$2
    echo -e "${COLOR}${TEXT}${NC}"
}

# Check for errors
check_error() {
    if [ $? -ne 0 ]; then
        print_color $RED "Error: $1"
        exit 1
    fi
}

# Validate environment
validate_env() {
    print_color $GREEN "Validating environment..."
    
    if [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ] || [ -z "$AZURE_TENANT_ID" ]; then
        print_color $RED "Azure credentials not set"
        exit 1
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        print_color $RED "OpenAI API key not set"
        exit 1
    fi
    
    if ! command -v az &> /dev/null; then
        print_color $RED "Azure CLI not installed"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_color $RED "kubectl not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_color $RED "docker not installed"
        exit 1
    }
}

# Build and push Docker image
build_and_push() {
    print_color $GREEN "Building and pushing Docker image..."
    
    # Get version from pyproject.toml
    VERSION=$(grep "version" pyproject.toml | cut -d'"' -f2)
    IMAGE_NAME="aiagentsregistry.azurecr.io/ai-agents:${VERSION}"
    
    # Build image
    docker build -t $IMAGE_NAME .
    check_error "Docker build failed"
    
    # Login to ACR
    az acr login --name aiagentsregistry
    check_error "ACR login failed"
    
    # Push image
    docker push $IMAGE_NAME
    check_error "Docker push failed"
    
    print_color $GREEN "Image built and pushed successfully"
}

# Deploy to AKS
deploy_to_aks() {
    ENV=$1
    print_color $GREEN "Deploying to AKS ($ENV)..."
    
    # Get AKS credentials
    az aks get-credentials --resource-group ai-agents-$ENV --name ai-agents-aks-$ENV
    check_error "Failed to get AKS credentials"
    
    # Apply Kubernetes configurations
    kubectl apply -f infrastructure/kubernetes/base/
    check_error "Failed to apply base configurations"
    
    kubectl apply -f infrastructure/kubernetes/overlays/$ENV/
    check_error "Failed to apply environment configurations"
    
    # Wait for deployment to complete
    kubectl rollout status deployment/ai-agents
    check_error "Deployment failed"
    
    print_color $GREEN "Deployment completed successfully"
}

# Setup monitoring
setup_monitoring() {
    print_color $GREEN "Setting up monitoring..."
    
    # Install Prometheus and Grafana
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring --create-namespace
    check_error "Failed to install monitoring stack"
    
    # Apply custom dashboards
    kubectl apply -f infrastructure/monitoring/dashboards/
    check_error "Failed to apply dashboards"
    
    print_color $GREEN "Monitoring setup completed"
}

# Run database migrations
run_migrations() {
    print_color $GREEN "Running database migrations..."
    
    # Apply Cosmos DB container definitions
    az cosmosdb sql container create \
        --account-name ai-agents-cosmos \
        --database-name ai_agents \
        --name knowledge_base \
        --partition-key-path "/id"
    check_error "Failed to create knowledge_base container"
    
    az cosmosdb sql container create \
        --account-name ai-agents-cosmos \
        --database-name ai_agents \
        --name legal_data \
        --partition-key-path "/id"
    check_error "Failed to create legal_data container"
    
    print_color $GREEN "Migrations completed"
}

# Deploy to environment
deploy_env() {
    ENV=$1
    
    if [ -z "$ENV" ]; then
        print_color $RED "Environment not specified"
        exit 1
    fi
    
    # Validate environment name
    case $ENV in
        dev|staging|prod) ;;
        *)
            print_color $RED "Invalid environment: $ENV"
            exit 1
            ;;
    esac
    
    print_color $YELLOW "Deploying to $ENV environment..."
    
    # Run deployment steps
    validate_env
    build_and_push
    deploy_to_aks $ENV
    setup_monitoring
    run_migrations
    
    print_color $GREEN "Deployment to $ENV completed successfully!"
}

# Check environment
check_env() {
    ENV=$1
    print_color $GREEN "Checking $ENV environment..."
    
    # Check AKS status
    kubectl get nodes
    check_error "Failed to get AKS nodes"
    
    # Check pods status
    kubectl get pods
    check_error "Failed to get pods"
    
    # Check services
    kubectl get services
    check_error "Failed to get services"
    
    print_color $GREEN "Environment check completed"
}

# Main menu
main_menu() {
    while true; do
        echo
        print_color $YELLOW "=== Deployment Tools ==="
        echo "1. Deploy to Development"
        echo "2. Deploy to Staging"
        echo "3. Deploy to Production"
        echo "4. Check Environment"
        echo "5. Exit"
        echo

        read -p "Choose an option: " choice

        case $choice in
            1) deploy_env "dev" ;;
            2) deploy_env "staging" ;;
            3) deploy_env "prod" ;;
            4) 
                read -p "Enter environment (dev/staging/prod): " env
                check_env $env
                ;;
            5) exit 0 ;;
            *) print_color $RED "Invalid option" ;;
        esac
    done
}

# Handle command line arguments
if [ $# -eq 0 ]; then
    main_menu
else
    case "$1" in
        "deploy")
            if [ -z "$2" ]; then
                print_color $RED "Environment not specified"
                exit 1
            fi
            deploy_env "$2"
            ;;
        "check")
            if [ -z "$2" ]; then
                print_color $RED "Environment not specified"
                exit 1
            fi
            check_env "$2"
            ;;
        *) print_color $RED "Unknown command: $1" ;;
    esac
fi