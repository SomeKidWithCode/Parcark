# Parcark
An OCR license plate-based carpark system.

Yes, trust.



(Ok, after having an existential crisis, I've decided to sanity check this system, because I checked my sanity and I can't find it)

stage 1, get the license plate
this is fine, that's already handled.
the only thing we have to do is wait for the ocr getter to get the same result 5 times

stage 2, a rfid card is scanned
this is where things start to catch fire
there are a couple things that we depend on for checking various states
first thing first, has this tag been registered?
a registered tag means a couple of things
the fuirst is tgat this tag has been formatted correctly and can be pulled off
it doesnt mean it have been registed in the bank though, that is seperate

so, the first thing to do is check if the card is a. registered and b. in the correct format
this service is provided by the RFIDTagRegister.verify method

now, this verifing process, can only give two results. true or false
so, what happens if the card is verified?
well it means we can charge from it
but, thus is the next check we need to commit and take note of: is this an entry or exit?
(we're going for realism here. as much as sir doesn't care, this not being the most strange unrealistic implementation ever will jelp my sanity, hpefulyl)
Ill repurpose the LPDatabase class for that
i'll use the license plate for this check, because it makes more sense
so, the first thing to look at for this is if the plate is already in the database
LPDatabase.query will handle this
(i might fix naming conventions later)

Now, the conditioosn
if the lp is already in the db, this must be an exit
this means we are going to charge
the LPDatabase.pull handles this
if it is not, this is an entry
LPDatabase.push handles thus
it also does the registration
(AT THE CURRENT POINT IN TIME, THERE IS A POTENTIAL ISSUE WITH PEOPLE RENTERYING THE CARPARK, CAUSING A DOUBLE REGISTER. I AM YET TO FIX THIS. it should be noted i could technically ignore this as the server already checks for double register but i would like to handle this myself and it sends you an error code)


Next is what if the card is not registered or in te right format?
well, we just ask to reformate and stuff, no big deal

after much frenzied typing, i think ive fix this system for now.
this is ready for testing



