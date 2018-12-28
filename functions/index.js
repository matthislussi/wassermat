const functions = require('firebase-functions');
const admin = require('firebase-admin');
const {BigQuery} = require('@google-cloud/bigquery');
const cors = require('cors')({ origin: true });

admin.initializeApp(functions.config().firebase);

const db = admin.database();

/**
 * Receive data from pubsub, then
 * Write telemetry raw data to bigquery
 * Maintain last data on firebase realtime database
 */
exports.receiveTelemetry = functions
	.region('europe-west1')
	.pubsub
	.topic('events')
	.onPublish((message, context) => {
		const attributes = message.attributes;
		const payload = message.json;

		const deviceId = attributes['deviceId'];

		const data = {
			humidity: payload.humidity,
			pumpActive: payload.pump_active,
			lightActive: payload.light_active,
			deviceId: deviceId,
			timestamp: context.timestamp
		};

		if (
			payload.humidity < 0 ||
			payload.humidity > 100
		) {
			// Validate and do nothing
			return;
		}

		return Promise.all([
			insertIntoBigquery(data),
			updateCurrentDataFirebase(data)
		]);
	});

/**
 * Maintain last status in firebase
 */
function updateCurrentDataFirebase(data) {
	return db.ref(`/devices/${data.deviceId}`).set({
		humidity: data.humidity,
		pumpActive: data.pumpActive,
		lightActive: data.lightActive,
		lastTimestamp: data.timestamp
	});
}

/**
 * Store all the raw data in bigquery
 */
function insertIntoBigquery(data) {
	const bigquery = new BigQuery();
	// console.log("insertIntoBigquery: "+functions.config().bigquery.datasetname)
	// TODO: Make sure you set the `bigquery.datasetname` Google Cloud environment variable.
	const dataset = bigquery.dataset(functions.config().bigquery.datasetname);
	// TODO: Make sure you set the `bigquery.tablename` Google Cloud environment variable.
	const table = dataset.table(functions.config().bigquery.tablename);

	return table.insert(data);
}

/**
 * Query bigquery with the last 7 days of data
 * HTTPS endpoint to be used by the webapp
 */
exports.getReportData = functions
	.region('europe-west1')
	.https.onRequest((req, res) => {
	const projectId = process.env.GCLOUD_PROJECT;
	const datasetName = functions.config().bigquery.datasetname;
	const tableName = functions.config().bigquery.tablename;
	const table = `${projectId}.${datasetName}.${tableName}`;

	const query = `
    SELECT 
      TIMESTAMP_TRUNC(data.timestamp, HOUR, 'Europe/Zurich') date_hour,
      avg(data.humidity) as avg_hum,
      min(data.humidity) as min_hum,
      max(data.humidity) as max_hum,
      count(*) as data_points      
    FROM \`${table}\` data
    WHERE data.timestamp between timestamp_sub(current_timestamp, INTERVAL 7 DAY) and current_timestamp()
    group by date_hour
    order by date_hour
  `;

	const bigquery = new BigQuery();
	return bigquery
		.query({
			query: query,
			useLegacySql: false
		})
		.then(result => {
			const rows = result[0];

			cors(req, res, () => {
				res.json(rows);
			});
		});
});
