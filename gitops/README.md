# KubeSage GitOps Installation Guide

This guide provides step-by-step instructions to set up and configure **Argo CD** (Argocd) using GitOps practices. This will help you manage your Kubernetes applications declaratively through version control.

## Prerequisites

Before proceeding with the installation, ensure you have the following prerequisites:

1. **Kubernetes Cluster**: A running Kubernetes cluster. You can use tools like Minikube, Kind, or any other Kubernetes provider.
2. **kubectl**: The Kubernetes command-line tool must be installed and configured to interact with your cluster.
3. **Access to Git Repository**: Ensure you have access to a Git repository where you will store your Kubernetes manifests. This example uses GitHub for simplicity.

## Installation Steps

### 1. Install Argo CD

Argo CD is an open-source continuous delivery tool for Kubernetes that automates the deployment of applications using GitOps principles.

#### Step 1: Create Namespace
First, create a dedicated namespace for Argo CD:

```bash
kubectl create ns argocd
```

#### Step 2: Deploy Argo CD Manifests

Apply the official Argo CD manifests from the GitHub repository:

```bash
kubectl apply \
    -n argocd \
    -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2. Access the Argo CD Server

Argo CD provides a web-based UI for managing your applications. By default, it is secured with basic authentication.

#### Step 1: Retrieve Initial Password

The initial admin password is stored as a Kubernetes secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
    --template '{{.data.password}}' | base64 -d
```

**Note**: Remember to replace `argocd` with your actual namespace if it's different.

#### Step 2: Login to Argo CD

Use the retrieved password to log in to the Argo CD server:

```bash
argocd login localhost:8080 --username admin --password <INITIAL_PASSWORD>
```

**Note**: Ensure that the Argo CD server is accessible on port `8080`. If running on a different host or using an Ingress, adjust the command accordingly.

### 3. Configure Git Repository

Configure your Git repository where your Kubernetes manifests are stored. This example uses GitHub with SSH authentication.

#### Step 1: Add Git Repository

Add your GitHub repository to Argo CD:

```bash
argocd repo add git@github.com:fdebar/kubesage.git --ssh-private-key-path ~/.ssh/my-private-key
```

**Note**: Replace `git@github.com:fdebar/kubesage.git` with the URL of your Git repository. Ensure that the SSH private key path (`~/.ssh/my-private-key`) is correct.

### 4. Deploy Applications

With Argo CD set up and configured, you can now deploy applications from your Git repository.

#### Step 1: Add Application

Add an application in Argo CD:

```bash
kubectl apply -f gitops/applications/my-app.yaml
```


#### Step 2: Sync the Application

Sync the application to apply the changes:

```bash
argocd app sync <APP_NAME>
```

**Example:**

```bash
argocd app sync my-app
```

### 5. Verify Deployment

To ensure that everything is working correctly, verify the status of your applications:

```bash
argocd app list
```

You can also access the Argo CD UI at `http://localhost:8080` to visually inspect and manage your deployments.
