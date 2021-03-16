# Overcloud Recommendations Service

This service is responsible for providing the recommendations for the different cloud accounts.


## Requirements

To scan an AWS account, there is a need to provide `aws_access_key_id` and `aws_secret_access_key` of an IAM user.
This user should have the following IAM policies
- `ReadOnlyAccess` - Built-in policy
- `PricingFullAcces` - A custom policy with the following JSON:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "pricing:DescribeServices",
                "pricing:GetAttributeValues",
                "pricing:GetProducts"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

## API Documentation

| Method        | API           | Body          | Description   |
| ------------- | ------------- | ------------- | ------------- |
| POST | /recommendations/scan | { "cloud_account": "604d60e89b81ec473cee1716" }| Scan the cloud account for recommendations |
| GET | /recommendations?cloud_account=\<id\> | N/A | Get recommendations for a specific cloud account |
| GET | /recommendations?cloud_account=\<id\>&recommendation=\<id\> | N/A | Get a specific recommendation for a specific cloud account |
| GET | /recommendations?cloud_account=\<id\>&recommendation=\<id\> | N/A | Get a specific recommendation for a specific cloud account |
| DELETE | /recommendations?cloud_account=\<id\> | N/A | Delete all recommendations for a specific cloud account (TODO) |
