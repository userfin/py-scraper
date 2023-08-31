#Берет csv документ, создает из него лист, собирает теги в отдельный лист.

import csv

def read_csv(file_name):
    with open(file_name, 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        template = [row for row in reader]
    template.pop(0)
    for row in template:
        row[5] = row[5].split(';')

    return template

def get_template_index(channel, template_list):
    template_index = 0
    for post_template in template_list:
          if channel in post_template:
              break
          elif template_index < len(template_list)-1:
              template_index +=1
    return template_index

# def parse_posting_template(article, template):
#     for row in template:
#         tags = row[2].split(';')
#         template_string = ''
#         for tag in tags:
#             #fix last spaces
#             template_string += f"{article['" + tag + "']}" + '\n\n'
#         row[2] = template_string
#         template_string = ''

#     return template

# def parse_tags(article, tags):
#     template_string = ''
#     for tag in tags:
#         #fix last spaces
#         template_string += f"{article}['" + {tag} + "']" + '\n\n'

#     return template_string
