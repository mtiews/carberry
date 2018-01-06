# Carberry - AWS Reporting and Analytics

This document describes the basic steps to persist and access the data submitted by the Carberry application with native AWS "Serverless" Services.

## Create S3 bucket to persist our data

Hint: Use some suffix/prefix to make your S3 bucket name unique, as the bucket name has to be unique across ALL bucket names. I'm using my AWS AccountId, which is unique across all AWS accounts. 

S3 Bucket Name: `smartcar-<AccountId>`

## What's missing?

AWS offers a lot of services, many of them derived and if you have a closer look at the details directly based on frameworks and tools from the Hadoop ecosystem, Presto, etc.

But one thing, a very important feature for performance improvements and cost reduction, is an "AWS native" way to create proper partitions using native AWS Services for your "Big Data" stored in AWS S3. 

We can persist the data using AWS Kinesis Firehose on AWS S3 quite simple...ETL the data via AWS Glue...create SQL-like access to the data via AWS Athena...hopefully create insights using AWS Quicksight...but to partition your data, we have to implement custom functionality? Ok, there are some AWS documents describing the approach, but - at least from my point of view - it breaks the "A Business Analyst can Setup the hole Story from Data to Analytical Insights..."
