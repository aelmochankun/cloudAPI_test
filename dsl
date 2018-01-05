GET _search
{
  "query": {
    "match_all": {}
  }
}

PUT description/
{
        "mappings": {
            "face": {
            "properties": {
                    "capture_date": {
                        "type" : "date",
                        "format": "yyyy-MM-dd HH:mm:ss"
                    },
                    "gender": {
                        "type" : "text",
                        "fielddata": true
                    },
                    "emotion": {
                        "type" : "text",
                        "fielddata": true
                    },
                    "age":{
                        "type" : "float"
                    }
                }
            }
        }
    }
    


POST description/face/_bulk
{"create": {"_id": "1"}}
{"capture_date": "1987-11-28 23:11:22"}
{"create": {"_id": "2"}}
{"capture_date": "1987-08-24 23:11:22"}

POST description/face/_bulk
{"update": {"_id": "1"}}
{"doc":{"capture_date": "1987-11-28 23:11:22","gender":"male"}}
{"update": {"_id": "2"}}
{"doc":{"capture_date": "1987-08-24 23:11:22"}}

GET description/face/_search


GET description/face/_search
{
  "sort": { "capture_date": "desc"}
}

DELETE description


GET description/face/_search
{
  "size": 0,
  "aggs": {
    "group_by_month": {
      "date_histogram": {
        "field": "capture_date",
        "interval": "minute"
      },
      "aggs": {
        "group_by_Type": {
          "terms": {
            "field": "gender"
          }
        }
      }
    }
  }
}
