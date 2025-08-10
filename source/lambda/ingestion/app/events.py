
from typing import Dict, Any, List

def records_from_event(event) -> List[Dict[str, Any]]:
    recs = []
    if (
        isinstance(event, dict)
        and event.get("source") == "aws.s3"
        and "detail" in event
    ):
        try:
            recs.append(
                {
                    "bucket": event["detail"]["bucket"]["name"],
                    "key": event["detail"]["object"]["key"],
                    "eventTime": event.get("time"),
                }
            )
        except Exception:
            pass
    if "Records" in event:
        for r in event["Records"]:
            try:
                recs.append(
                    {
                        "bucket": r["s3"]["bucket"]["name"],
                        "key": r["s3"]["object"]["key"],
                        "eventTime": r.get("eventTime"),
                    }
                )
            except Exception:
                continue
    return recs
