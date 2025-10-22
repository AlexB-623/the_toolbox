from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random
from os import getcwd
from flask_login import login_required

cwd = getcwd()
gibbergen_blueprint = Blueprint('gibbergen', __name__, template_folder='templates/gibbergen')

clean_verb_path = f'{cwd}/gibbergen/data/ing_words_clean.json'
clean_tech_path = f'{cwd}/gibbergen/data/tech_terms_clean.json'


def get_verbs(path):
    with open(path) as json_verb_file:
        data = json.load(json_verb_file)
        return data


def get_terms(path):
    with open(path) as json_tech_file:
        data = json.load(json_tech_file)
        return data

def term_maker():
    verbs = get_verbs(clean_verb_path)
    terms = get_terms(clean_tech_path)
    num_verbs = len(verbs)
    num_terms = len(terms)
    verb_choice = str(random.randint(1,num_verbs))
    term_choice = str(random.randint(1, num_terms))
    verbing = verbs[verb_choice]
    termicle = terms[term_choice]
    verbs = []
    terms = []
    gibberish = f'{verbing} the {termicle}...'
    return gibberish


@gibbergen_blueprint.route('/')
def gibbergen():
    term = term_maker()
    return render_template('gibbergen_home.html', term=term)



@gibbergen_blueprint.route('/sampler')
@login_required
def gibbergen_sampler():
    term_list = []
    i = range(1, 10)
    for n in i:
        term = term_maker()
        term_list.append(term)
    return render_template('sampler.html', terms=term_list)