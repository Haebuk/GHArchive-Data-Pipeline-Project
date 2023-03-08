import polars as pl

schema = {
    "id": pl.Utf8,
    "type": pl.Utf8,
    "actor": pl.Struct(
        {
            "id": pl.Int32,
            "login": pl.Utf8,
            "display_login": pl.Utf8,
            "gravatar_id": pl.Utf8,
            "url": pl.Utf8,
            "avatar_url": pl.Utf8,
        }
    ),
    "repo": pl.Struct(
        {
            "id": pl.Int32,
            "name": pl.Utf8,
            "url": pl.Utf8,
        }
    ),
    "payload": pl.Struct(
        {
            "push_id": pl.Utf8,
            "size": pl.Int32,
            "distinct_size": pl.Int32,
            "ref": pl.Utf8,
            "head": pl.Utf8,
            "before": pl.Utf8,
            "commits": pl.List(
                pl.Struct(
                    {
                        "sha": pl.Utf8,
                        "author": pl.Struct(
                            {
                                "email": pl.Utf8,
                                "name": pl.Utf8,
                            }
                        ),
                        "message": pl.Utf8,
                        "distinct": pl.Boolean,
                        "url": pl.Utf8,
                    }
                ),
            ),
        }
    ),
    "public": pl.Boolean,
    "created_at": pl.Datetime,
    "org": pl.Struct(
        {
            "id": pl.Int32,
            "login": pl.Utf8,
            "gravatar_id": pl.Utf8,
            "url": pl.Utf8,
            "avatar_url": pl.Utf8,
        }
    ),
    "other": pl.Utf8,
}
