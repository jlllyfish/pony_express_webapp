#let birthday(
  name : "",
  firstname : "",
  birthday: "",
  age: "",
  ..superfluous_arguments
  ) = [
    #set page(
      paper: "a6",
      fill: blue
    )
    
    #text(40pt, [Happy Birthday #firstname #name])

    #pagebreak()
    #text(30pt, [Since you were born on #birthday])

    #text(30pt, [You are #emph[#age years old] this year])

  ]