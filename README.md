
Conda environment to recreate the system: package-list.txt

use: # $ conda create --name <env> --file package-list.txt

I intended to create a separate environment for production and debugging with different 
levels of logging, etc. The skeletop for it should be functional but I didn't have the time 
to refine it. I used ./RunDebug.sh during development.

Note than in app/tests there's just the output of reportGenXML.py 
(when run standalone __name__ == "__main__"). These tests are not as exhaustive as I'd 
wanted but I think the conversion procedures themselves are quite solid and I tried quite
 hard to break them within their constraints.

All the routes are in views and should be self-explanatory.

'/' and '/index' show the query to the database. XMLs are generated on demand when 
the file is missing. The path /xmls lists the reports previously generated.

On generation /xml/<id> I didn't do MIME or redirection but a simple 
link to the newly generated file. I thought it was a minor priority. The templates are pretty 
basic and based off a version of bootstrap I had around, to save time.

XML generation which is very generic and allows for almost anything you throw at it.

