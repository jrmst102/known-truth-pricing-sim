# Known-Truth Pricing Simulation

This project provides the Python pilot implementation for the book chapter
*Data and Machine-Learning Foundations for AI-Enhanced Price Optimization: From
Prediction to Prescription and Decision Reliability*, by Dr. Jose Mendoza,
Clinical Associate Professor at New York University.

The pilot supports the chapter's work on evaluating machine-learning methods for
price optimization using reproducible, known-truth simulations calibrated with
Dominick's data.

The software is provided under the [MIT License](LICENSE). This license applies
to the code, not to the data; see the [Data section](#data) for the applicable
data terms.

## Data

Download Dominick's data in accordance with the
[Kilts Center's terms](https://www.chicagobooth.edu/research/kilts/research-data/dominicks).
Do not redistribute movement, demographics, or customer-count data. The MIT
License covers this project's code only; the datasets remain subject to their
own terms.

Existing archives and UPC CSV files in `data/` can be used directly. Put new
downloads in `data/raw/`. SAS does not need to be installed to use CSV ZIP
archives or SAS7BDAT files. The supplied SAS conversion script is retained for
reference and is not run by the project.

Calibration requires the `wsna`, `upcsna`, `wtna`, `upctna`, `wtti`, and
`upctti` category files. Each can be a CSV, a ZIP containing one dataset, or a
SAS7BDAT file. The store metadata must include `store`, `price_tier`, and
`zone`; demographic data alone does not provide the research pricing zones.

Contact:
Professor Jose Mendoza
New York University
jose.mendoza@nyu.edu
