# Airline-Prediction-System

An end-to-end distributed Big Data pipeline designed to process, aggregate, and visualize over **6.4 million commercial airline records** using **Hadoop HDFS, Hadoop MapReduce Streaming, Apache Cassandra, and Streamlit**.

Deployed Link: https://airline-prediction-system.onrender.com/
## 🏛️ System Architecture

```text
┌─────────────────┐
│  Raw 2009.csv   │
│  6.4M Records   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Hadoop HDFS   │
│ /airline_data/  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Hadoop MapReduce│
│ Python Streaming│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Apache Cassandra │
│ carrier_metrics │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Streamlit +     │
│ Plotly Dashboard│
└─────────────────┘
```

### Architecture Components

1. **Storage Tier:** Stores raw airline data in Hadoop Distributed File System (HDFS).
2. **Compute Tier:** Processes distributed data using Hadoop MapReduce and Python streaming scripts.
3. **Serving Tier:** Stores aggregated airline performance metrics in Apache Cassandra.
4. **Analytics Tier:** Provides an interactive Streamlit dashboard with Plotly visualizations and scenario-based risk analysis.

## 📁 Repository Structure

```text
airline_project/
│
├── docker-compose.yml       # Docker infrastructure configuration
├── hadoop.env               # Hadoop environment variables
├── mapper.py                # MapReduce mapper
├── reducer.py               # MapReduce reducer
├── carrier_metrics.csv      # Aggregated airline metrics
├── app.py                   # Streamlit dashboard
├── README.md                # Project documentation
└── .gitignore               # Excluded files and datasets
```

**Note:** The raw `2009.csv` dataset is not included in the repository because it exceeds GitHub's 100 MB file limit. Place the dataset in the project directory before running the pipeline.

## ⚙️ Tech Stack

- **Big Data Processing:** Apache Hadoop 3.2.1, MapReduce Streaming
- **Distributed Storage:** Hadoop HDFS
- **NoSQL Database:** Apache Cassandra
- **Backend Processing:** Python
- **Dashboard:** Streamlit
- **Data Visualization:** Plotly
- **Data Manipulation:** Pandas
- **Containerization:** Docker and Docker Compose

## 📋 Prerequisites

Install the following before starting:

- Docker Desktop with Docker Compose
- Python 3.8 or later
- Required Python packages: Streamlit, Pandas, and Plotly
- The airline dataset `2009.csv`
- Project files, including `mapper.py`, `reducer.py`, `app.py`, and `docker-compose.yml`

## 🚀 Setup and Execution

### 1. Start Docker Containers

Ensure Docker Desktop is running and execute the following command from the project directory:

```bash
docker-compose up -d
```

Check the running containers:

```bash
docker ps
```

Ensure the Hadoop NameNode, DataNode, and Cassandra containers are running.

### 2. Initialize Apache Cassandra

Open the Cassandra query shell:

```bash
docker exec -it cassandra_db cqlsh
```

Execute the following CQL commands:

```sql
CREATE KEYSPACE IF NOT EXISTS airline_analytics
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE airline_analytics;

CREATE TABLE IF NOT EXISTS carrier_metrics (
    carrier text PRIMARY KEY,
    total_flights bigint,
    total_delay_min double,
    avg_delay_min double,
    total_cancelled bigint,
    cancellation_rate double
);
```

Exit the shell:

```sql
exit;
```

### 3. Upload the Dataset to HDFS

Ensure that `2009.csv` is present in the project directory and accessible at `/workspace/2009.csv` inside the NameNode container.

Normalize Python script line endings:

```bash
docker exec -it namenode sed -i 's/\r$//' /workspace/mapper.py
docker exec -it namenode sed -i 's/\r$//' /workspace/reducer.py
```

Create the HDFS input directory:

```bash
docker exec -it namenode hdfs dfs -mkdir -p /airline_data/input
```

Upload the dataset:

```bash
docker exec -it namenode hdfs dfs -put -f /workspace/2009.csv /airline_data/input/
```

Remove an existing output directory if one exists:

```bash
docker exec -it namenode hdfs dfs -rm -r /airline_data/output
```

If the output directory does not exist, Hadoop may report an error for the removal command. You can continue.

### 4. Execute the Hadoop MapReduce Job

Run the Hadoop Streaming job:

```bash
docker exec -it namenode sh -c "cd /workspace && hadoop jar /opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar -D mapreduce.job.reduces=1 -files mapper.py,reducer.py -mapper 'python3 mapper.py' -reducer 'python3 reducer.py' -input /airline_data/input/2009.csv -output /airline_data/output"
```

The mapper extracts relevant flight information, while the reducer aggregates metrics by airline carrier.

**Expected output characteristics:**

- Approximately 6.4 million input records
- Aggregated metrics grouped by carrier
- Output written to `/airline_data/output/part-00000`

Actual counts depend on the dataset and the mapper and reducer implementations.

### 5. Export Aggregated Results to Cassandra

Extract the MapReduce output into a local CSV file:

```bash
docker exec -it namenode bash -c "hdfs dfs -cat /airline_data/output/part-00000 | tr '\t' ',' > /workspace/carrier_metrics.csv"
```

Copy the file into the Cassandra container:

```bash
docker cp carrier_metrics.csv cassandra_db:/carrier_metrics.csv
```

Load the results into Cassandra:

```bash
docker exec -it cassandra_db cqlsh -e "COPY airline_analytics.carrier_metrics (carrier, total_flights, total_delay_min, avg_delay_min, total_cancelled, cancellation_rate) FROM '/carrier_metrics.csv' WITH DELIMITER = ',';"
```

If you need to replace previously loaded results, truncate the table before importing:

```bash
docker exec -it cassandra_db cqlsh -e "TRUNCATE airline_analytics.carrier_metrics;"
```

**Important:** Ensure that the exported file contains only valid data rows in the expected column order. Remove Hadoop log messages and any headers if your reducer output includes them.

Verify the imported data:

```bash
docker exec -it cassandra_db cqlsh -e "SELECT * FROM airline_analytics.carrier_metrics LIMIT 5;"
```

### 6. Install Dashboard Dependencies

Install the Python packages:

```bash
pip install streamlit pandas plotly
```

### 7. Launch the Streamlit Dashboard

From the project directory, run:

```bash
streamlit run app.py
```

Open the dashboard in your browser:

http://localhost:8501

Ensure Cassandra is running and that the connection settings in `app.py` match your Docker configuration.

## 📊 Dashboard Features

### Summary Metrics
- Total flights evaluated
- Number of airline carriers
- Average departure delay
- Airline cancellation statistics

### Interactive Visualizations
- Average departure delay by airline
- Historical cancellation rates
- Airline performance comparisons using Plotly charts

### Scenario-Based Risk Prediction
- Interactive inputs for flight conditions
- Scenario comparisons for higher- and lower-risk conditions
- Analysis of factors such as departure time, day of the week, and route distance, where supported by the implemented prediction logic

### Benchmark Scenarios
- **Best-Case Scenario:** Simulates conditions associated with lower delay risk.
- **Worst-Case Scenario:** Simulates conditions associated with higher delay risk.

These scenarios depend on the assumptions and calculations implemented in `app.py`; they should not be interpreted as guaranteed predictions.

### Cassandra Audit Table
View aggregated carrier metrics queried directly from the `airline_analytics.carrier_metrics` table.

## 📈 Project Workflow

1. Load the airline dataset into HDFS.
2. Process flight records using Hadoop MapReduce Streaming.
3. Aggregate flight delays and cancellation metrics by carrier.
4. Export the results from HDFS.
5. Store the aggregated metrics in Apache Cassandra.
6. Visualize the results through an interactive Streamlit dashboard.

## 🔒 Dataset and Repository Notes

The raw dataset is excluded from Git tracking because of its size.

To keep it out of future commits, ensure `.gitignore` contains:

```gitignore
2009.csv
```

The dataset must be obtained separately and placed in the project directory before executing the complete pipeline.

## 🎯 Project Objective

FlightOps demonstrates how distributed storage, batch processing, NoSQL data serving, and interactive analytics can be combined into an end-to-end Big Data application for airline operational analysis.

The project focuses on scalable data processing, carrier-level performance aggregation, and accessible visualization of airline delay and cancellation patterns.
