# spotify-wrapped

To update functions: 
```
firebase deploy --only functions
```

To set up on a new machine, first install firebase cli, then run:

```
firebase login
```

Link to Logs for Firebase Cloud Function: https://console.cloud.google.com/logs/query;query=%2528resource.type%3D%22cloud_function%22%20resource.labels.function_name%3D%2528%22spotify_polling%22%2529%20resource.labels.region%3D%22us-central1%22%2529%20OR%20%2528resource.type%3D%22cloud_run_revision%22%20resource.labels.service_name%3D%2528%22spotify-polling%22%2529%20resource.labels.location%3D%22us-central1%22%2529;cursorTimestamp=2024-12-24T01:14:02.202855Z;startTime=2024-12-24T00:35:58.500Z;endTime=2024-12-24T01:24:13.500Z?authuser=0&project=olivia-spotify-wrapped&hl=en
