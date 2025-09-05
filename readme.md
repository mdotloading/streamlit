# Stock App - Cloud Deployment (Kubernetes) Aufgabe 3

Stock App to fetch tickers and display them including various indicators to overlay onto the chart. 
Dockerfiles are included for containerization. Containerization and cloud deployment files are not included in this version since it was for a school project and includes API Keys to my universities Cloud. 

- **Backend:** Flask on Port **5000** (`mdotloading/stock-backend:vX`)
- **Frontend:** Streamlit on Port **8501** (`mdotloading/stock-frontend:vX`)
- **Ingress:** Traefik (`web`, `websecure`)


To run the backend flask server: python "name_of_file".py
To run the streamlit frontend: streamlit run "name_of_file".py