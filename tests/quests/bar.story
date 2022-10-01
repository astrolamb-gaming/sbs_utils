shared barkeep = faces.random_torgoth()

shared martinis = 10
shared beer = 10
shared vodka = 8

============== GotoBar ===================

face barkeep
"""""""""""""""""""""""""""""""""
Thirty?
I have
"""""""""""""""""""""""""""""""""
^^^    {martinis} Martinis^^^ if martinis > 0
^^^    {beer} beers^^^ if beer > 0
^^^    {"and " if (beer+martinis) > 0 else ""}{vodka} vodka^^^ if vodka > 0
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
...
nothing
....
I'm all out. 
If you go to DS1 and get more supply them the Next one is on me.
^^^^^^^^^^^^ if martinis == 0 and vodka == 0 and beer ==0

choices
    + "Martini"-> Martinis if martinis > 0
    + "Beer" -> Beer if beer > 0
    + "Vodka" -> Vodka if vodka > 0
    + "Had enough" <<- if (beer+martinis+vodka) > 0

# it gets here when there are no more buttons
# delay to give a chance to read
delay 5s

area 40 20 70 70
face barkeep
row
"""""""""""""""""""""""""""""""""""
BAR is closed until more supplies arrive
they are available at DS1
"""""""""""""""""""""""""""""""""""

choices
delay 5s
<<-

===================Vodka======================
shared vodka = vodka-1
refresh GotoBar
->GotoBar

======================Beer======================
shared beer = beer-1
refresh GotoBar
->GotoBar

======================Martinis======================
shared martinis = martinis-1
refresh GotoBar
->GotoBar
