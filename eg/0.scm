(define (main) 
  (print (spawn #f (lambda ()
                     (whee (list 'a)))))
  (print 'yo))

(define (whee x)
  (print (cons x (cons 'b '()))))
