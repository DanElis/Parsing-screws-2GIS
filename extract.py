#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import argparse
import sys
import string
import re
import pickle

list_simple_colors = ['серый',
                      'черный',
                      'белый',
                      'красный',
                      'желтый',
                      'зеленый',
                      'синий',
                      'фиолетовый',
                      'пурпурный',
                      'оранжевый',
                      'коричневый',
                      'хаки',
                      'ультрамарин',
                      'хром',
                      'золотой',
                      'бронзовый',
                      'голубой',
                      'слоновая кость',
                      'синяя вода',
                      'шоколадный',
                      'красное вино'
                      ]
list_shade = ['темно',
              'светло',
              'земельно',
              'шоколадно',
              'ярко',
              'рубиново',
              'небесно',
              'рубиново',
              'винно',
              ]
list_short_shade = ['т-',
                    'т.',
                    'темн-',
                    'темн.',
                    'с-',
                    'с.',
                    'свет-',
                    'свет.',
                    'св.',
                    'св-',
                    'яр.',
                    'яр-',
                    'яр.-',
                    'слон.'
                    ]
list_complex_colors = ['слоновая кость',
                       'синяя вода',
                       'красное вино']
list_not_color = ['гол.']
dict_short_to_full_shade = {'т-': 'темно-',
                            'т.': 'темно',
                            'темн-': 'темно',
                            'темн.': 'темно',
                            'с-': 'светло',
                            'с.': 'светло',
                            'свет-': 'светло-',
                            'свет.': 'светло',
                            'св.': 'светло',
                            'св-': 'светло-',
                            'яр.': 'ярко',
                            'яр-': 'ярко-',
                            'яр.-': 'ярко-',
                            'слон.': 'слоновая'
                            }

dict_typos = {'золото': 'золотой',
              'бронза': 'бронзовый',
              'серебро': 'серебряный',
              }


SATURATED = 'насыщенный'
ZINC = 'цинк'


def parse_title(title):
    diameter = np.nan
    length = np.nan
    color = ''
    try:
        diameter, length = get_diameter_and_length(title)
        color = get_color(title)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print('failed to parse string')
        print(f'exception:{e}')

    return length, diameter, color


def get_diameter_and_length(line):
    length = np.nan
    diameter = np.nan
    for i in indices_separator(line):
        diameter = get_number(line, i, -1)
        length = get_number(line, i, 1)
        if not (np.isnan(diameter) or np.isnan(length)):
            break
        length = np.nan
        diameter = np.nan
    if np.isnan(length) and np.isnan(diameter):
        length = get_length(line)
    return diameter, length


def get_number(line, i_sep, sign):
    has_dot = False
    is_first_num = False
    tmp_str = ''
    num = np.nan
    if 0 < i_sep + sign < len(line) and line[i_sep + sign] == ' ':
        i_sep += sign
    for ch in line[i_sep + sign::sign]:
        if ch.isdigit():
            is_first_num = True
            tmp_str += ch
        elif (ch == ',' or ch == '.') and not has_dot and is_first_num:
            has_dot = True
            tmp_str += '.'
        else:
            break
    if len(tmp_str) != 0:
        num = float(tmp_str[::sign])
    return num


def indices_separator(line):
    indices = []
    for line in re.finditer(r'[*XxхХ/]', line):
        indices.append(line.start())
    return indices


def get_length(line):
    length = np.nan
    indices = [line.start() for line in re.finditer(r'мм', line)] + [line.start() for line in re.finditer(r'mm', line)]
    for i in indices:
        length = get_number(line, i, -1)
    return length


def get_color(title):
    color = ''
    shade = ''
    title_prep = preparing_title_for_color(title)
    words = title_prep.split()

    has_zinc = ZINC in words
    has_saturated = SATURATED in words

    for (w, i) in zip(words, range(len(words))):
        if is_shade(w):
            shade = get_shade(w, is_shade_=True)
        if is_color(w):
            color += f'{w} '
    color = color.strip()
    color = get_initial_form_color(color, shade, has_zinc, has_saturated)
    if color == '':
        if has_ral(title):
            color = get_ral(title)

    return color


def has_ral(title):
    return title.lower().find('ral') != -1


def get_ral(title):
    title = title.lower()
    title = title.replace('-', ' ').replace('(', ' ')
    words = title.split()
    color = ''
    for w, i in zip(words, range(len(words))):
        if w == 'ral' and i + 1 < len(words) and words[i + 1].isdigit():
            color = f'RAL {words[i + 1]}'
    return color


def preparing_title_for_color(title):
    title = title.lower()
    title += ' '
    title = title.replace('ые', 'ый').replace('ие', 'ий')
    title = title.replace('ё', 'е')
    for c in list_not_color:
        title = title.replace(c, ' ')
    list_short_shade_without_punctuation = [sh.translate(sh.maketrans({key: "" for key in string.punctuation})) for
                                            sh in list_short_shade]

    for (sh, sh_w) in zip(list_short_shade, list_short_shade_without_punctuation):
        title = title.replace(f'{sh} ', f'{sh_w} ')

    for short, full in dict_short_to_full_shade.items():
        title = title.replace(short, full)

    for typo, correct in dict_typos.items():
        title = title.replace(typo, correct)

    punctuation = string.punctuation.replace('-', '')
    title = title.translate(title.maketrans({key: " " for key in punctuation}))
    return title


def is_shade(word):
    is_shade_ = False
    for sh in list_shade:
        if word == sh:
            is_shade_ = True
    return is_shade_


def get_initial_form_color(str_colors, shade, has_zinc, has_saturated):
    main_color = ''
    list_c = split_str_colors(str_colors)
    for col in list_c:
        if not shade:
            shade = get_shade(col)
        w = delete_shade(col)
        for c in list_simple_colors:
            if c.find(w) != -1:
                main_color += f'{c} '
                break
    main_color = main_color.strip()
    if has_zinc:
        main_color += f' {ZINC}'
    if not main_color:
        shade = ''
    if has_saturated and main_color:
        main_color += f' {SATURATED} '
    color = f'{shade}{main_color}'
    color = color.strip()
    return color


def split_str_colors(str_colors):
    list_colors = str_colors.split()
    join_colors = []
    for color in list_colors:
        for complex_color in list_complex_colors:
            if complex_color.find(color) != -1:
                join_colors.append(color)
    for jc in join_colors:
        list_colors.remove(jc)
    if join_colors:
        list_colors.append(' '.join(join_colors))
    return list_colors


def get_shade(word, is_shade_=False):
    shade = ''
    if is_shade_:
        for sh in list_shade:
            if word == sh:
                shade = f'{sh}-'
    else:
        for sh in list_shade:
            if word.find(sh) == 0:
                shade = f'{sh}-'

    return shade


def delete_shade(word):
    for sh in list_shade:
        word = word.replace(sh, '')
    for sh in list_shade:
        if word.find('-') != -1:
            word = word.replace(sh, '')

    word = word.replace('-', '')
    return word


def is_color(word):
    word_without_shade = delete_shade(word)

    is_color_ = False
    for c in list_simple_colors:
        if c.find(word_without_shade) != -1 and len(word_without_shade) > 2:
            is_color_ = True
    return is_color_


if __name__ == "__main__":
    file_name = ''
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name', nargs='?')
    args = parser.parse_args()
    if args.file_name:
        file_name = args.file_name
    else:
        print('file name not entered')
        exit(0)

    df = pd.read_csv(file_name)

    df_out = df['title'].apply(lambda x: pd.Series(parse_title(x)))
    df_out.columns = ['length', 'diameter', 'color']
    df_out['id'] = df['id']
    df_out = df_out[['id', 'length', 'diameter', 'color']]
    df_out.to_csv('out-attributes.csv')
