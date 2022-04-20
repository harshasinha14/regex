from app import app
from flask import render_template, request, jsonify, Response
from app.config import serverconfig, entity_config
import pandas as pd
import numpy as np
import re
from werkzeug.utils import secure_filename
import os
from spacy import displacy

#UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route("/")
def home():
    """Renders the home page with basic template and few(upload button, input text box)"""
    return render_template('home.html', home=True, entity_list=entity_config.entity_list,
                           embed_type=entity_config.embed_type, question_list=entity_config.sample_question_list,
                           selected_ques='others')


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/run_extract", methods=['GET', 'POST'])
def run_extract():
    """Renders the eqa_run, where the output will be rendered to home.html with all the conditions
    implemented
    """
    print("Inside Model run")
    context_text = ''
    ques_text = ''
    eqa_text = ''
    if request.method == 'POST':

        read_file = request.files['file']
        keyword = request.form['text_area']
        filename = secure_filename(read_file.filename)
        read_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        processed_df = process_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), filename)
        result_df = matcher(processed_df, keyword)
        formatted_df = custom_highlighter(result_df)

        col_names = ['Extracted_Paragraph']
        ui_table = formatted_df.head()[col_names].values.tolist()

        #output_dict = formatted_df.head().to_dict()
        output_dict = {'results':"This is the sample text"}

    return render_template("home.html", error=True, tables=ui_table, show_table=True, col_names=col_names, file = output_dict)


def process_file(path, filename):
    #from PyPDF2 import PdfFileReader
    import sys, fitz
    #input_file = PdfFileReader(open(path, 'rb'))
    doc = fitz.open(path)
    total_content_raw = []
    total_content_lower = []
    for page in doc:  # iterate the document pages
        text = page.get_text().encode("utf8")  # get plain text (is in UTF-8)
        text1 = page.get_text('text')
        res = text1.split('.\n \n')
        con = [i for i in text1.split('.\n \n')]
        # return concatenated content
        total_content_raw.extend(con)
        total_content_lower.extend([i.lower() for i in con])
        df = pd.DataFrame({'text_raw': total_content_raw, 'text_lower': total_content_lower})
    return df


def matcher(df, keyword):
    def _helper_matcher(row, keyword):
        iter = re.finditer(keyword, row)
        locations = [m.span() for m in iter]
        if locations:
            return True, locations
        else:
            return False, None

    df['output'] = df.text_lower.apply(lambda row: _helper_matcher(row, keyword))
    mask_df = df['output'].apply(lambda row: pd.Series(row))
    mask_df.columns = ['is_present', 'location']
    print()
    final_df = pd.concat([df.drop(columns=['output'], axis=0), mask_df], axis=1)
    return final_df


def custom_highlighter(output_df):
    colors = {'': '#f18cd3'}
    output_df.fillna('', inplace=True)
    entity_list = ['']
    for ind, val in output_df.iterrows():
        ents = []
        text = val['text_lower']
        extracted_coord = val['location']
        for each_coord in extracted_coord:
            ents.append((each_coord[0], each_coord[1], entity_list[0]))
        ents = sorted(ents)
        ents_sorted = [{"start": elem[0], "end": elem[1], "label": elem[2]} for elem in ents]
        custom = {'text': text, 'ents': ents_sorted}
        options = {"ents": entity_list, "colors": colors}
        output_df.loc[ind, 'Extracted_Paragraph'] = displacy.render(custom, style="ent", manual=True, options=options)

    return output_df

@app.route('/download/')
def download_file():
    print("====inside the download======")
    output_dict = request.args.get('filename')
    print("------------", eval(output_dict).keys())
    if 'results' in eval(output_dict).keys():
        print("====#===", eval(output_dict))
        df = pd.DataFrame(eval(output_dict), index=[0])
    else:
        df = pd.DataFrame(eval(output_dict))
    # rearranging the columns for download
    output_df = df.copy()
    return Response(output_df.to_csv(index=False), mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=output.csv"})





if __name__ == "__main__":
    app.run(debug=True)

