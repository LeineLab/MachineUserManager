# -*- coding: utf-8 -*-

"""
Variable names that will be replaced:
{NAME}              Username
{CARD_HEX}          Short hexadecimal representation of card UID
{CARD_DEC}          Long decimal representation of card UID
{CREDIT_REMAINING}  Remaining credit of card
{TIME_REMAINING}    Remaining time (if currently logged in just credit / PRICE_MINUTE, otherwise (credit - PRICE_ONCE) / PRICE_MINUTE)
{PRICE_ONCE}        Price for starting a session
{PRICE_MINUTE}      Price per minute logged in (not respecing actual usage time, just the time "blocking" the machine)}

Text will be padded by whitespaces on the right and cropped to 20 chars
"""

TEMPLATE = [
    #01234567890123456789
    "",
    "",
    "",
    "",
]

MACHINE_OFF = [
    "",
    "  Turn on machine",
    "     to login.",
    "",
]

MACHINE_READY = [
    "Hold tag/card close",
    "  to the reader to",
    "       login.",
    "",
]

# HAS COUNTDONW
CARD_UNAUTHORIZED = [
    " This card is not",
    " authorized to use",
    "   this machine.",
    "",
]

# HAS COUNTDONW
CARD_UNKNOWN = [
    "  This tag is not",
    "     registred.",
    "{CARD_HEX}",
    "",
]

# HAS COUNTDONW
CREDIT_TOO_LOW = [
    "{NAME}",
    "Credit: {CREDIT_REMAINING}",
    "Credit too low.",
    "Please recharge.",
]

LOGIN = [
    "{NAME}",
    "Credit: {CREDIT_REMAINING}",
    "Once {PRICE_ONCE}+{PRICE_MINUTE}/Min",
    "Green: Yes / Red: No",
]

LOGGED_IN = [
    "Unlocked by:",
    "{NAME}",
    "Remaining time:",
    "{TIME_REMAINING} Min",
]

DB_UNAVAILABLE = [
    "Datenbase currently",
    "unavailable.",
    "Please try again",
    "later.",
]
