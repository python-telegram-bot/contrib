# Extra functionality for PTB keyboards

### This module contains extended keyboard classes with extra functionality for PTB keyboards.

### Methods is self-descriptive.

```python
class IExtendedInlineKeyboardMarkup(ABC, ):
    """ Popular keyboard actions """

    def to_list(self, ) -> list[list[InlineKeyboardButton]]:
        
    def find_btn_by_cbk(self, cbk: str, ) -> tuple[InlineKeyboardButton, int, int] | None:
        """ Returns buttons, row index, column index if found, None otherwise """
        
    def get_buttons(self, ) -> list[InlineKeyboardButton]:
        """ Just get flat list of buttons of the keyboard """

    def split(
            self,
            buttons_in_row: int,
            buttons: Sequence[InlineKeyboardButton] | None = None,
            update_self: bool = True,
            empty_rows_allowed: bool = True,
            strict: bool = False,
    ) -> list[list[InlineKeyboardButton]]:
        """
        Split keyboard by N buttons in row.
        Last row will contain remainder,
        i.e. num of buttons in the last row maybe less than `buttons_in_row` parameter.

        Possible enhancement:
            keep_empty_rows: bool - keep empty rows in final keyboard if not enough buttons.
            # Please create feature issue if you need it.
        """
```

## Requirements

*   `python-telegram-bot>=20.0`

## Authors

*   [David Shiko](https://github.com/david-shiko)
