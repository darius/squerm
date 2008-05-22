(define (main)
  (spawn #f main-process))

(define (main-process ? !)
  (let ((sub! (spawn #f subprocess)))
    (sub! (list 'hello !))
    (print (list 'main-got-back (?)))))

(define (subprocess ? !)
  (let ((msg (?)))
    (print (list 'sub-got (car msg)))
    ((cadr msg) 'reply)))
