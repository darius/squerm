(define (main)
  (spawn main-process))

(define (main-process ? !)
  (let ((sub! (spawn subprocess)))
    (sub! (list 'hello !))
    (print (list 'main-got-back (?)))))

(define (subprocess ? !)
  (let ((msg (?)))
    (print (list 'sub-got (car msg)))
    ((cadr msg) 'reply)))

(define (print x)
  (write x)
  (newline))
