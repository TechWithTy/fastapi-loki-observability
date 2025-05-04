Getting started with the OpenTelemetry Collector and Loki tutorial

The OpenTelemetry Collector offers a vendor-agnostic implementation of how to receive, process, and export telemetry data. With the introduction of the OTLP endpoint in Loki, you can now send logs from applications instrumented with OpenTelemetry to Loki using the OpenTelemetry Collector in native OTLP format. In this example, we will teach you how to configure the OpenTelemetry Collector to receive logs in the OpenTelemetry format and send them to Loki using the OTLP HTTP protocol. This will involve configuring the following components in the OpenTelemetry Collector:

    OpenTelemetry Receiver: This component will receive logs in the OpenTelemetry format via HTTP and gRPC.
    OpenTelemetry Processor: This component will accept telemetry data from other otelcol.* components and place them into batches. Batching improves the compression of data and reduces the number of outgoing network requests required to transmit data.
    OpenTelemetry Exporter: This component will accept telemetry data from other otelcol.* components and write them over the network using the OTLP HTTP protocol. We will use this exporter to send the logs to the Loki native OTLP endpoint.

Dependencies

Before you begin, ensure you have the following to run the demo:

    Docker
    Docker Compose

    Tip

    Alternatively, you can try out this example in our interactive learning environment: Getting started with the OpenTelemetry Collector and Loki tutorial.

    It’s a fully configured environment with all the dependencies already installed.

    Interactive

    Provide feedback, report bugs, and raise issues for the tutorial in the Grafana Killercoda repository.

Scenario

In this scenario, we have a microservices application called the Carnivorous Greenhouse. This application consists of the following services:

    User Service: Manages user data and authentication for the application. Such as creating users and logging in.
    Plant Service: Manages the creation of new plants and updates other services when a new plant is created.
    Simulation Service: Generates sensor data for each plant.
    Websocket Service: Manages the websocket connections for the application.
    Bug Service: A service that when enabled, randomly causes services to fail and generate additional logs.
    Main App: The main application that ties all the services together.
    Database: A database that stores user and plant data.

Each service generates logs using the OpenTelemetry SDK and exports to the OpenTelemetry Collector in the OpenTelemetry format (OTLP). The Collector then ingests the logs and sends them to Loki.
Step 1: Environment setup

In this step, we will set up our environment by cloning the repository that contains our demo application and spinning up our observability stack using Docker Compose.

    To get started, clone the repository that contains our demo application:
    bash 

git clone -b microservice-otel-collector  https://github.com/grafana/loki-fundamentals.git

Next we will spin up our observability stack using Docker Compose:
bash

docker compose -f loki-fundamentals/docker-compose.yml up -d

To check the status of services we can run the following command:
bash

    docker ps -a

        Note

        The OpenTelemetry Collector container will show as Stopped or Exited (1) About a minute ago. This is expected as we have provided an empty configuration file. We will update this file in the next step.

After we’ve finished configuring the OpenTelemetry Collector and sending logs to Loki, we will be able to view the logs in Grafana. To check if Grafana is up and running, navigate to the following URL: http://localhost:3000
Step 2: Configuring the OpenTelemetry Collector

To configure the Collector to ingest OpenTelemetry logs from our application, we need to provide a configuration file. This configuration file will define the components and their relationships. We will build the entire observability pipeline within this configuration file.
Open your code editor and locate the otel-config.yaml file

The configuration file is written using YAML configuration syntax. To start, we will open the otel-config.yaml file in the code editor:

    Open the loki-fundamentals directory in a code editor of your choice.
    Locate the otel-config.yaml file in the loki-fundamentals directory (Top level directory).
    Click on the otel-config.yaml file to open it in the code editor.

You will copy all three of the following configuration snippets into the otel-config.yaml file.
Receive OpenTelemetry logs via gRPC and HTTP

First, we will configure the OpenTelemetry receiver. otlp: accepts logs in the OpenTelemetry format via HTTP and gRPC. We will use this receiver to receive logs from the Carnivorous Greenhouse application.

Now add the following configuration to the otel-config.yaml file:
yaml

# Receivers
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

In this configuration:

    receivers: The list of receivers to receive telemetry data. In this case, we are using the otlp receiver.
    otlp: The OpenTelemetry receiver that accepts logs in the OpenTelemetry format.
    protocols: The list of protocols that the receiver supports. In this case, we are using grpc and http.
    grpc: The gRPC protocol configuration. The receiver will accept logs via gRPC on 4317.
    http: The HTTP protocol configuration. The receiver will accept logs via HTTP on 4318.
    endpoint: The IP address and port number to listen on. In this case, we are listening on all IP addresses on port 4317 for gRPC and port 4318 for HTTP.

For more information on the otlp receiver configuration, see the OpenTelemetry Receiver OTLP documentation.
Create batches of logs using a OpenTelemetry processor

Next add the following configuration to the otel-config.yaml file:
yaml

# Processors
processors:
  batch:

In this configuration:

    processors: The list of processors to process telemetry data. In this case, we are using the batch processor.
    batch: The OpenTelemetry processor that accepts telemetry data from other otelcol components and places them into batches.

For more information on the batch processor configuration, see the OpenTelemetry Processor Batch documentation.
Export logs to Loki using a OpenTelemetry exporter

We will use the otlphttp/logs exporter to send the logs to the Loki native OTLP endpoint. Add the following configuration to the otel-config.yaml file:
yaml

# Exporters
exporters:
  otlphttp/logs:
    endpoint: "http://loki:3100/otlp"
    tls:
      insecure: true

In this configuration:

    exporters: The list of exporters to export telemetry data. In this case, we are using the otlphttp/logs exporter.
    otlphttp/logs: The OpenTelemetry exporter that accepts telemetry data from other otelcol components and writes them over the network using the OTLP HTTP protocol.
    endpoint: The URL to send the telemetry data to. In this case, we are sending the logs to the Loki native OTLP endpoint at http://loki:3100/otlp.
    tls: The TLS configuration for the exporter. In this case, we are setting insecure to true to disable TLS verification.
    insecure: Disables TLS verification. This is set to true as we are using an insecure connection.

For more information on the otlphttp/logs exporter configuration, see the OpenTelemetry Exporter OTLP HTTP documentation
Creating the pipeline

Now that we have configured the receiver, processor, and exporter, we need to create a pipeline to connect these components. Add the following configuration to the otel-config.yaml file:
yaml

# Pipelines
service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp/logs]

In this configuration:

    pipelines: The list of pipelines to connect the receiver, processor, and exporter. In this case, we are using the logs pipeline but there is also pipelines for metrics, traces, and continuous profiling.
    receivers: The list of receivers to receive telemetry data. In this case, we are using the otlp receiver component we created earlier.
    processors: The list of processors to process telemetry data. In this case, we are using the batch processor component we created earlier.
    exporters: The list of exporters to export telemetry data. In this case, we are using the otlphttp/logs component exporter we created earlier.

Load the configuration

Before you load the configuration into the OpenTelemetry Collector, compare your configuration with the completed configuration below:
yaml

# Receivers
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
        
# Processors
processors:
  batch:

# Exporters
exporters:
  otlphttp/logs:
    endpoint: "http://loki:3100/otlp"
    tls:
      insecure: true
      
# Pipelines
service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp/logs]

Next, we need apply the configuration to the OpenTelemetry Collector. To do this, we will restart the OpenTelemetry Collector container:
bash

docker restart loki-fundamentals-otel-collector-1

This will restart the OpenTelemetry Collector container with the new configuration. You can check the logs of the OpenTelemetry Collector container to see if the configuration was loaded successfully:
bash

docker logs loki-fundamentals-otel-collector-1

Within the logs, you should see the following message:
console

2024-08-02T13:10:25.136Z        info    service@v0.106.1/service.go:225 Everything is ready. Begin running and processing data.

Stuck? Need help?

If you get stuck or need help creating the configuration, you can copy and replace the entire otel-config.yaml using the completed configuration file:
bash

cp loki-fundamentals/completed/otel-config.yaml loki-fundamentals/otel-config.yaml
docker restart loki-fundamentals-otel-collector-1

Step 3: Start the Carnivorous Greenhouse

In this step, we will start the Carnivorous Greenhouse application. To start the application, run the following command:

    Note

    This docker-compose file relies on the loki-fundamentals_loki docker network. If you have not started the observability stack, you will need to start it first.

bash

docker compose -f loki-fundamentals/greenhouse/docker-compose-micro.yml up -d --build 

This will start the following services:
console

 ✔ Container greenhouse-db-1                 Started                                                         
 ✔ Container greenhouse-websocket_service-1  Started 
 ✔ Container greenhouse-bug_service-1        Started
 ✔ Container greenhouse-user_service-1       Started
 ✔ Container greenhouse-plant_service-1      Started
 ✔ Container greenhouse-simulation_service-1 Started
 ✔ Container greenhouse-main_app-1           Started

Once started, you can access the Carnivorous Greenhouse application at http://localhost:5005. Generate some logs by interacting with the application in the following ways:

    Create a user.
    Log in.
    Create a few plants to monitor.
    Enable bug mode to activate the bug service. This will cause services to fail and generate additional logs.

Finally to view the logs in Loki, navigate to the Loki Logs Explore view in Grafana at http://localhost:3000/a/grafana-lokiexplore-app/explore.
Summary

In this example, we configured the OpenTelemetry Collector to receive logs from an example application and send them to Loki using the native OTLP endpoint. Make sure to also consult the Loki configuration file loki-config.yaml to understand how we have configured Loki to receive logs from the OpenTelemetry Collector.
Further reading

For more information on the OpenTelemetry Collector and the native OTLP endpoint of Loki, refer to the following resources:

    Loki OTLP endpoint
    How is native OTLP endpoint different from Loki Exporter
    OpenTelemetry Collector Configuration

Complete metrics, logs, traces, and profiling example

If you would like to use a demo that includes Mimir, Loki, Tempo, and Grafana, you can use Introduction to Metrics, Logs, Traces, and Profiling in Grafana. Intro-to-mltp provides a self-contained environment for learning about Mimir, Loki, Tempo, and Grafana.

The project includes detailed explanations of each component and annotated configurations for a single-instance deployment. Data from intro-to-mltp can also be pushed to Grafana Cloud.