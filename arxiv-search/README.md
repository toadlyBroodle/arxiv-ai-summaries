# arXiv search

This script allows you to query the arXiv API using various search parameters. You can search for papers by title, author, abstract, category, and more. The script supports logical operators to refine your search queries.

## Usage

To use the script, run the following command:

```bash
python review_bot.py "search_query" [options]
```

### Required Argument

- `search_query`: The search query for arXiv. Combine fields and terms using logical operators. Use `+` to represent spaces in search terms.

### Optional Arguments

- `--start`: The starting index for results (default: 0).
- `--max_results`: The maximum number of results to return (default: 10).
- `--sort_by`: Sort by field. Choices are `relevance`, `lastUpdatedDate`, `submittedDate` (default: relevance).
- `--sort_order`: Sort order. Choices are `ascending`, `descending` (default: descending).

### Example Usage

```bash
python review_bot.py "cat:cs.AI+OR+cat:cs.LG" --max_results 5 --sort_by submittedDate
python review_bot.py "ti:quantum+OR+ti:relativity" --sort_order ascending
```


## Search Fields

- `ti`: Title
- `au`: Author
- `abs`: Abstract
- `co`: Comment
- `jr`: Journal reference
- `cat`: Category
- `rn`: Report number
- `all`: All fields

## Logical Operators

- `AND`
- `OR`
- `ANDNOT`

## Categories

Category codes listed at [arXiv taxonomy](https://arxiv.org/category_taxonomy).

## License

Copyright (C) 2024 Landon Mutch.
I'm not liable for anything you do with this code.
Do whatever you want with it.