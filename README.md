> This project requires python 3.7 as some some features implemented within this project 
> utilize only currently available in this version

> To run the script simply open a command promt and navigate to the directory
> in which this file is found. Then run the commands:

> to ensure that you have the necessary packages you can optionally run this first

pip install -r requirements.txt

> Then start the main script by running the next line. Note that if you don't
> provide an exact match you will be prompted to enter the ID of the procedure
> to retrieve data for or to pull all matches' data from the site. It's important 
> to be aware that if you hit "A" when prompted to pull all matches that if it says
> there were a significant amount of matches it can only be stopped by a Keyboard
> Interrupt by the user. There is a 11.5 second wait for this process to be done, but
> that alone may not prevent the the site from requesting the reCAPTCHA.

> The `search_term` below is Case Sensitive, so if you type "arm mri" you won't receive
> any matches. This should be a future change in functionality as it requires the user 
> navigate through the same pages to see if they've got it in the right case or order.
> Essentially, this case & order sensitivity is a problem that minimizes the utility
> of this project and should be an immediate change to the current process.

Python Requester.py --search_term MRI --search_type Procedure --zip_code 37221

> This will output all the data for the "green" locations for whichever procedure(s)
> is/are provided into an XLSX file held in the Results folder downloaded/created by 
> running the above command.
