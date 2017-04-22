from __future__ import print_function, absolute_import

from io import open

from flask import render_template
from app import app

import os
import json
from os.path import exists
from app.reportGenXML import generateXMLFile
import logging

from time import ctime

try:
    from os import scandir
except ImportError:
    from scandir import scandir  # use scandir PyPI module on Python < 3.5


LOG = logging.getLogger("appReportGen.log")

data_dir = os.path.join(app.root_path, "data/")
reports_xml_dir = os.path.join(app.root_path, "static/reports_xml/")


# just a bit of eye candy. Only shows the first 127-130 chars of the report JSON
@app.context_processor
def utility_processor():
    def format_long_string(long_string):
        if len(long_string)>130:
            return long_string[0:127] + "..."
        else: return long_string
    return dict(format_long_string=format_long_string)


@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # db.session.rollback() # not altering the DB at the moment
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
# @app.route('/index/<int:page>', methods = ['GET', 'POST'])
def index():
    records = map(lambda x: (x.name, ctime(os.path.getmtime(x.path)),),
                  filter(lambda a: a.is_file(), (i for i in scandir(data_dir))))

    return render_template('index.html', title='Home', records=records)


# @app.route('/xml/<int:id>')
@app.route('/xml/<id>')
def xml(id):
    reports_xml_fname = reports_xml_dir+'/reports_%s.xml' % id
    if not exists(reports_xml_fname):
        print("generating", reports_xml_fname)

        with open(data_dir + id, "r", encoding="utf8") as f_data:
            file_contents = f_data.read()
            obj_report = json.loads(file_contents)
            generateXMLFile(obj_report, reports_xml_fname)  # quite self-explanatory
    return render_template( 'singlelink.html', link = '/static/reports_xml/reports_%s.xml' % id )


@app.route('/xml/')
def xmls():
    """ lists pregenerated XML reports"""
    reports_xml_dir = os.path.join(app.root_path, "static/reports_xml")    
    ldir = filter(lambda a: a !='.DS_Store', os.listdir(reports_xml_dir))
    return render_template('xmls.html', id = id, ldir = ldir)


