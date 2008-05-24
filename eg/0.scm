(define (main) 
  (print (spawn #f (lambda ()
                     (whee (list 'a)))))
  (print 'yo))

(define (whee x)
  (print `(,x b))
  (print (cons x (cons 'b '()))))
