# Overcloud Recommendations Service

This service is responsible of providing the recommendations for the different cloud accounts.


## API Documentation

| Method        | API        | Description   |
| ------------- | ------------- | ------------- |
| POST | /recommendations/scan | Scan the cloud account for recommendations  |
| GET | /recommendations?cloud_account=\<id\>  | Get recommendations for a specific cloud account  |
| GET | /recommendations?cloud_account=\<id\>&recommendation=\<id\>  | Get a specific recommendation for a specific cloud account  |
