# Carberry - AWS Reporting and Analytics

This document describes the basic steps to persist and access the data submitted by the Carberry application with native AWS "Serverless" Services.

## Create S3 bucket to persist our data

Hint: Use some suffix/prefix to make your S3 bucket name unique, as the bucket name has to be unique across ALL bucket names. I'm using my AWS AccountId, which is unique across all AWS accounts. 

S3 Bucket Name: `smartcar-<AccountId>`

## Create Firehose Delivery streams to persist raw data in AWS S3

The following schema will be applied to the structure in S3:

Usage data will be split according to the `source` field in the submitted JSON documents:
* OBD2 data: `carberry/data/obd2/` + ` AWS Firehose specific suffix`
* GPS data: `carberry/data/gps/` + `AWS Firehose specific suffix`

Status data will be put here:
* `carberry/status/` + `Firehose specific suffix`

For each prefix a separate Firehose delivery stream has to be created, which all point to the `smartcar-<accountId>` bucket.

To reduce the amount of stored data and costs for AWS Athena (pricing is based on the size of bytes parsed per query execution) I select `GZIP` for the S3 compression option.

After this step we have three Firehose delivery streams, one for each prefix:
* Stream `carberry-data-obd2` pointing to bucket `smartcar-<accountId>` with prefix `carberry/data/obd2/`
* Stream `carberry-data-obd2` pointing to bucket `smartcar-<accountId>` with prefix `carberry/data/gps/`
* Stream `carberry-data-obd2` pointing to bucket `smartcar-<accountId>` with prefix `carberry/status/`

...which are waiting waiting to receive their data from AWS IoT Core...

## Feeding the AWS IoT messages to AWS Kinesis Firehose

To feed the message from AWS IoT to AWS Kinesis Firehose we have to create rules, which allow basic filtering and transformation of the incomming data, and triggering actions (like sending the data to AWS Kinesis Firehose).

For each Rule we have to define an SQL statement and an action.

We are using the following statements, to feed the data in the appropriate AWS Kinesis Firehose streams:

For `carberry-data-obd2`:
```
SELECT * as data, timestamp as timestamp, clientid() as clientid, topic() as topic, timestamp() as received FROM 'carberry/+/data' WHERE source = 'obd2'
````

For `carberry-data-gps`:
```
SELECT * as data, timestamp as timestamp, clientid() as clientid, topic() as topic, timestamp() as received FROM 'carberry/+/data' WHERE source = 'gps'
````

For `carberry-status`:
```
SELECT * as data, timestamp as timestamp, clientid() as clientid, topic() as topic, timestamp() as received FROM 'carberry/+/status'
````

## What's missing?

AWS offers a lot of services, many of them derived and if you have a closer look at the details directly based on frameworks and tools from the Hadoop ecosystem, Presto, etc.

But one thing is - at the time of writing - missing, a very important feature for performance improvements and cost reduction. That's an "AWS native" way to create proper partitions using native AWS Services for your "Big Data" stored in AWS S3. 

We can persist the data using AWS Kinesis Firehose on AWS S3 quite simple...ETL the data via AWS Glue...create SQL-like access to the data via AWS Athena...hopefully create insights using AWS Quicksight...but to partition your data, we have to implement custom functionality? Ok, there are some AWS documents describing the approach, but - at least from my point of view - it breaks the "A Business Analyst can Setup the hole Story from Data to Analytical Insights..."
