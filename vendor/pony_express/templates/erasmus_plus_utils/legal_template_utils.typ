#let legal_title(content) = align(center,
  box(inset: (y:20pt),strong(smallcaps(content)))
)

#let article_count = counter("article")
#let mention_count = counter("mention")

#let article_navy = rgb("#16235C")

#let article(it) = block(above: 26pt, below: 10pt, sticky: true)[
  #article_count.step()
  #mention_count.update(0)
  #text(11.5pt, weight: "bold", fill: article_navy)[Article #context article_count.display() : #it]
  #v(-4pt)
  #line(length: 100%, stroke: 0.8pt + article_navy)
]

#let mention(it) = block(breakable: false,[
  #mention_count.step()
  #text(
    9.5pt,
    {
      let width = 1em
      grid(
        columns: (2.2em, 1fr),
        gutter: 0.6em,
        [#context article_count.display().#context mention_count.display() ],
        [#it] 
      )
    }
  )
]
)



