A quick guide to load testing Grafana Loki with Grafana k6
Christian Haudum

Christian Haudum
• 2022-06-08 • 8 min

As a software engineer here at Grafana Labs, I’ve learned there are two questions that commonly come up when someone begins setting up a new Loki installation: “How many logs can I ingest into my cluster?” followed by, “How fast can I query these logs?”

There are two ways to find out the answers.

You could configure your existing application infrastructure to push logs and see what happens — or you can find out the smart way and load test the system with Grafana k6.

Grafana k6 is a modern load-testing tool. Its clean and approachable scripting API works locally or in the cloud. Thankfully, there is also a k6 extension that allows you to push logs to and query logs from Loki. It acts as a Loki client, simulating real-world load to test the scalability, reliability, and performance of your Loki installation.

In this post, I’m going to explain how to do that and show you the basic concepts for write and query path testing, as well as some more insights on how to use configuration options to tune your tests. In my explanation, I will assume you have a basic understanding of how to use k6. (If you’re new to it, head over the documentation — it’s great!) Also, I’m not going to explain how to build and install the k6 Loki extension, but it’s not as hard as you might think. You can find instructions here.

Once the extension is built, you can use the resulting binary to execute a load test file that is written in Javascript. In the JS file, you can use the API provided by the xk6-loki extension. The instructions themselves are not executed by the JS runtime, but are just function calls of binary code. That way, it combines the performance of compiled Go code for generating log lines and performing network requests, and the flexibility of scripting in Javascript.

A very basic test.js load test file looks like this:

import loki from 'k6/x/loki';

const timeout = 5000; // ms
const conf = loki.Config("http://localhost:3100", timeout);
const client = loki.Client(conf);

export default () => {
   client.push();
};

And can be executed like so:

./k6 run test.js
Pushing logs

First, let’s look at how to randomize push requests to simulate write path load. As shown in the example above, the Client object has a method push(). This generates a single push request with a payload containing five streams with random label values and a total uncompressed size of log files between 800Kb and 1Mb.

Need to adjust the request parameters? The client also has a pushParameterized(streams, minSize, maxSize) method that lets you do exactly that. In the following example, the push request generates a random amount between two and eight streams, and a total log size between 1 and 2MB.

import loki from 'k6/x/loki';

const conf = loki.Config("http://localhost:3100");
const client = loki.Client(conf);

export default () => {
   let streams = randInt(2, 8);
   client.pushParameterized(streams, 1024*1024, 2*1024*1024);
};

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
};

If you want a constant batch size, set the second and third argument to the same value. The size for each individual stream is the total size divided by the number of streams.

In terms of the actual log lines, xk6-loki generates log lines using the flog library, which generates fake log lines in various common log formats, such as apache_common, syslog rfc5424, or json. The log line format is defined by the format label of the stream.
Labels and streams

So far, we’ve controlled the format and size of the actual logs, but did not have a look at the log metadata, also called labels. A set of labels with unique key-value-pairs is called a stream, and a stream contains many log lines. When using the pushParameterized(n, minSize, maxSize) function to push logs to Loki, xk6-loki creates n streams with random label values.

A stream always contains three predefined labels — instance, os, and format — as well as optional labels namespace, app, pod, language, and word. The predefined label instance is set to the VU and hostname; os is one of windows, linux, or darwin; and format is one of the supported log formats of flog.

Optional labels are used when the Config object is instantiated with a “label cardinality” map. The map defines how many different label values for the given label name should be used. It allows you to control how many unique streams the load test can possibly generate, which iis just the cartesian product of the possible values.

The following example shows how to configure the cardinality of optional labels.

import loki from 'k6/x/loki';

const labels = {
  "namespace": 2,
  "app": 5,
};
const conf = loki.Config("http://localhost:3100", 10000, labels);
const client = loki.Client(conf);

Assuming the test is run from a single machine with 10 VUs, the maximum amount of unique streams is:

# instance x os x format x namespace x app
10 x 3 x 6 x 2 x 5 = 1800 streams

At the time of writing, there is no way to define custom label names.
Querying logs

As with pushing logs, the Client object also provides functions for querying logs and metadata from Loki. Just like Loki’s query API endpoints, these methods are:

    instantQuery(query, limit)
    rangeQuery(query, duration, limit)
    labelsQuery(duration)
    labelValuesQuery(label, duration)
    seriesQuery(matchers, duration)

(They do very much what their names suggest.)

The following example uses the labels from the Config object to generate randomized LogQL queries. Since the pool of labels is generated already when the Config object is instantiated — and because it is done with a fixed seed — label names and values are generated in a predictable manner. This is useful when you want to run a write and a read load test separately.

import {check} from 'k6';
import loki from 'k6/x/loki';

const conf = loki.Config("http://localhost:3100");
const client = loki.Client(conf);

export default () => {

  // Pick a random log format from label pool
  let format = randomChoice(conf.labels\["format"]);

  // Execute instant query with limit 1
  res = client.instantQuery(`count_over_time({format="${format}"}[15m])`, 1)
  // Check for successful read
  check(res, { 'successful instant query': (res) => res.status == 200 });

  // Execute range query over last 15m and limit 1000
  res = client.rangeQuery(`{format="${format}"}`, "15m", 1000)
  // Check for successful read
  check(res, { 'successful range query': (res) => res.status == 200 });
}

function randomChoice(items) {
  return items\[Math.floor(Math.random() * items.length)];
}

When performing query tests, it’s important to always check the response of the API call, as it gives further insights into whether queries were successful or not.
Single user vs multi-tenancy

Loki can be run in single and multi-tenant mode. When run in single-tenant mode, all logs are stored under the same tenant: “fake.” In multi-tenant mode, the client can specify the X-Scope-OrgID header to identify as a tenant. Logs stored by a specific tenant can only be retrieved by the same tenant. xk6-loki also supports both modi operandi.

If Loki is configured in multi-tenant mode (authentication enabled), and the loki.Config method does not receive a username as part of the URL, xk6-loki will use a different X-Scope-OrgID value (in the format xk6-tenant-$VU) for each virtual user (VU). That means that running a test with n VUs will ingest roughly 1/n of the total logs for each VU. The same applies for queries, so a query for a tenant only processes 1/n of the total data ingested.

If Loki is configured in multi-tenant mode but you want to use xk6-loki in single user mode, you can specify the username, and optionally also the password, in the user info part of the URL. It would look like this:

`const conf = loki.Config(“http://username[:password]@localhost:3100”)`

This way, every request, both for pushing and querying logs, is done using the same X-Scope-OrgID header across all VUs on the load test.

Unlike single user mode, which optionally accepts a password, multi-tenant mode does not allow authorization (passwords) of individual tenants.
Monitoring your load test

Last but not least, what would a load test be without gathering hard data that you can analyze and compare? In addition to the build-in metrics of k6, the extension collects additional custom metrics — both for push and query requests — and they are printed in the end-of-test summary. Here’s an example of what one looks like:
End-of-test summary of an ordinary test run
End-of-test summary of an ordinary test run

For query requests, these metrics are exposed:

    loki_bytes_processed_total
    loki_bytes_processed_per_second
    loki_lines_processed_total
    loki_lines_processed_per_second

loki_bytes_processed_total and loki_lines_processed_total are counters for bytes and lines respectively.

loki_bytes_processed_per_second and loki_lines_processed_per_second are throughput rates for bytes and lines respectively.

All four metrics are derived from the query response statistics sent by the Loki server.

And for push requests, you’ll want to use:

    loki_client_lines
    loki_client_uncompressed_bytes

loki_client_lines is a counter that counts the total number of lines that have been pushed to Loki during the time of the load test. loki_client_uncompressed_bytes counts the total number of bytes of the pushed log lines.

These metrics provide insights in how much data was transferred to and processed by Loki.