# Citations for Building a CLI Tool in Python

## References

1. [Python argparse documentation](https://docs.python.org/3/library/argparse.html)
2. [Click library for CLI](https://click.palletsprojects.com/)
3. [Typer - Modern CLI framework](https://typer.tiangolo.com/)
4. [Python CLI best practices](https://docs.python-guide.org/writing/cli/)

## Code Examples

```python
import argparse


def main():
    parser = argparse.ArgumentParser(description="A sample CLI tool")
    parser.add_argument("--name", help="Your name")
    args = parser.parse_args()
    print(f"Hello, {args.name}!")
```

## Further Reading

- [Building Command Line Interfaces in Python](https://realpython.com/command-line-interfaces-python-argparse/)
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46)