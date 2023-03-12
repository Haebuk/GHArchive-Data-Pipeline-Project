import polars as pl

PL_SCHEMA = {
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
    "public": pl.Boolean,
    "created_at": pl.Utf8,
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
