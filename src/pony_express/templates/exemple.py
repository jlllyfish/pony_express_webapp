import os
import time
from copy import deepcopy
from enum import Enum

from pony_express.service.grist import not_in_grist
from pony_express.service.utils import get_date_from_timestamp
from pony_express.service.ponyexpress import generate_pdf_from_grist
from slugify import slugify
'''
# Access informations to the Grist Data
'''
GRIST_SERVER = None #not needed for doc on the official server
GRIST_TEAM_SITE = os.environ['GRIST_TEAM_SITE']
GRIST_DOC_ID = os.environ['GRIST_DOC_ID']
GRIST_TABLE = os.environ['GRIST_TABLE']
GRIST_PDF_COLUMN = None # None to prevent upload else "carte"  

'''
Access information to the TYPST template
'''
TEMPLATE_NAME = "birthday"
TEMPLATE_FILENAME = "birthday_template"
TEMPLATE_FOLDERNAME = "exemple" # the column type must be "Attachment"

"""
Definition of all the information required by the PDF
the name of the enum must be the name of the Typst parameter (ex: birthday)
the value of the enum must be the name of the column in Grist (ex: Date_d_anniversaire)
"""
class PERSON_DATA(Enum):
    name = "Nom"
    firstname = "Prenom"
    birthday = "Date_d_anniversaire"
    age = not_in_grist("age")

"""
Return true if all lines from the table must be exported and treated
Add condition if any must be omitted
"""
def should_be_exported(record: dict) -> bool:
    if PERSON_DATA.birthday.value in record:
        # ignore the line if the exemple is in the future
        return record[PERSON_DATA.birthday.value] < time.time()
    else:
        return False

def name_pdf(record) -> str:
    return slugify(record[PERSON_DATA.name.name]+" "+record[PERSON_DATA.firstname.name]+"_birthday")


"""
Can be used to add any treatment of the data exported from grist
for instance, date format, address validation etc...
"""
def apply_data_transformation(dict) -> dict:
    transformed_dict = deepcopy(dict)
    transformed_dict[PERSON_DATA.birthday.name] = get_date_from_timestamp(dict[PERSON_DATA.birthday.name])
    transformed_dict[PERSON_DATA.age.name] = calculate_age(dict[PERSON_DATA.birthday.name])
    return transformed_dict


def calculate_age(birthday) -> int:
    now = time.time()
    duration_in_seconds = now - birthday
    years = divmod(duration_in_seconds, 31536000)[0]  # Seconds in a year=365*24*60*60 = 31536000.
    return round(years)

if __name__ == '__main__':
    print("GENERATE BIRTHDAY CARD")
    generate_pdf_from_grist(
        GRIST_DOC_ID,
        GRIST_TEAM_SITE,
        GRIST_TABLE,
        PERSON_DATA,
        TEMPLATE_FOLDERNAME,
        TEMPLATE_FILENAME,
        TEMPLATE_NAME,
        should_be_exported,
        apply_data_transformation,
        name_pdf,
        GRIST_SERVER,
        GRIST_PDF_COLUMN
    )
