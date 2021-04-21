# Overcloud Recommendations Service

This service is responsible for providing the recommendations for the different cloud accounts.

## Requirements

To scan an AWS account, there is a need to provide `aws_access_key_id` and `aws_secret_access_key` of an IAM user. This
user should have the following IAM policies

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

If you want the system to be able to remediate the recommendations as well, you'll need to add the following permissions
to the user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DeleteVolume",
      ],
      "Resource": "*"
    }
  ]
}
```

## Start Service

To start the recommendation service, run the following command:

```bash
python manage.py runserver
```

# API Documentation

## Scan Recommendations

This path will scan the cloud account for recommendations

| Method | Path             |
| :----- | :--------------- |
| `POST` | `/recommendations/scan` |

### Parameters

- `cloud_account` `(string: <required>)` – The ID of the cloud account to scan

### Sample Payload

```json
{
  "cloud_account": "60526ffb3a611c4670f2a38a"
}
```

### Sample Request

```bash
$ curl \
    --request POST \
    --data @payload.json \
    http://localhost:5000/recommendations/scan
```

## Read Recommendations

This endpoint retrieves the recommendations for a specific cloud account

| Method | Path                                         |
| :----- | :------------------------------------------- |
| `GET`  | `/recommendations?cloud_account=:cloud-account-id&recommendation_type=recommendation-type` |

### Parameters

- `cloud-account-id` `(string: <required>)` – The ID of the cloud account
- `recommendation-type` `(string: "")` - Specifies the recommendation type to retrieve. If not set all recommendations
  are returned

### Sample Request

```shell-session
# All recommendations
$ curl http://localhost:5000/recommendations?cloud_account=60526ffb3a611c4670f2a38a

# Specific recommendation
$ curl http://localhost:5000/recommendations?cloud_account=60526ffb3a611c4670f2a38a&recommendation_type=UnattachedVolumes
```

### Sample Response

```json
{
  "recommendations": [
    {
      "_id": {
        "$oid": "60660e9b4c92137be7140413"
      },
      "accountId": "60526ffb3a611c4670f2a38a",
      "collectTime": "01/04/2021, 21:19:07",
      "data": [
        {
          "createTime": "17/03/2021",
          "id": "vol-0aa5d8bb9f8f210e3",
          "price": "0.1000000000",
          "priceUnit": "GB-Mo",
          "region": "us-east-1",
          "size": 1,
          "totalPrice": "0.1000",
          "type": "gp2"
        }
      ],
      "name": "Unattached Volumes",
      "totalPrice": "0.6",
      "type": "UnattachedVolumes"
    }
  ],
  "status": "ok"
}
```

## Remediate Recommendations

This path will remediate the provided recommendations

| Method | Path             |
| :----- | :--------------- |
| `POST` | `/recommendations/remediate` |

### Parameters

- `cloud_account` `(string: <required>)` – The ID of the cloud account to scan
- `recommendation_type` `(string: "")` – The type of the recommendation to remediate. If not provided, will remediate
  all

### Sample Payload

```json
{
  "cloud_account": "60526ffb3a611c4670f2a38a",
  "recommendation_type": "UnassociatedEIP"
}
```

### Sample Request

```bash
$ curl \
    --request POST \
    --data @payload.json \
    http://localhost:5000/recommendations/remediate
```

## Validate Cloud Account

This path will validate the cloud account

| Method | Path             |
| :----- | :--------------- |
| `POST` | `/cloud-accounts/validate` |

### Parameters

- `cloudProvider` `(string: <required>)` – The ID of the cloud account to scan
- `accessKey` `(string: <required>)` – The access key of the AWS user
- `secretKey` `(string: <required>)` – The secret access key of the AWS user

### Sample Payload

```json
{
  "cloudProvider": "AWS",
  "accessKey": "XXXXX",
  "secretKey": "XXXXX"
}
```

### Sample Request

```bash
$ curl \
    --request POST \
    --data @payload.json \
    http://localhost:5000/cloud-accounts/validate
```
